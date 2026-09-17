"""Poison message handling for Kafka consumers.

RabbitMQ gives a message a lifecycle: reject it and the broker moves it to a
retry queue, counts the attempts in a header and eventually dead-letters it.
Kafka has none of that. A message that always fails is redelivered forever, and
because a partition is read in order, everything behind it stops with it.

So the same outcome is assembled by hand: retry a few times in place, then
publish the message to a dead letter topic and commit past it, which is what
FR-08 asks for when a packet cannot be accepted.

The attempt counter lives in memory, keyed by partition and offset, so it
resets when the consumer restarts. A production system would keep it in the
database or carry it in headers on republish.
"""

import json
import logging
from collections import defaultdict

from confluent_kafka import Producer

log = logging.getLogger("poison")

MAX_ATTEMPTS = 3


class PoisonHandler:
    def __init__(self, bootstrap: str, dlt_topic: str, consumer_name: str):
        self._producer = Producer({"bootstrap.servers": bootstrap, "acks": "all"})
        self._dlt_topic = dlt_topic
        self._consumer_name = consumer_name
        self._attempts = defaultdict(int)

    def should_retry(self, msg) -> bool:
        """Count this failure and say whether the message deserves another try."""
        key = (msg.partition(), msg.offset())
        self._attempts[key] += 1
        return self._attempts[key] < MAX_ATTEMPTS

    def send_to_dlt(self, msg, error: str) -> None:
        """Publish the failed message to the dead letter topic.

        The original payload is kept intact and the diagnostic context goes into
        headers, so whoever investigates sees both what arrived and why it was
        rejected.
        """
        key = (msg.partition(), msg.offset())

        self._producer.produce(
            topic=self._dlt_topic,
            key=msg.key(),
            value=msg.value(),
            headers=[
                ("original_topic", msg.topic()),
                ("original_partition", str(msg.partition())),
                ("original_offset", str(msg.offset())),
                ("consumer", self._consumer_name),
                ("error", error[:500]),
                ("attempts", str(self._attempts[key])),
            ],
        )
        self._producer.flush(10)
        self._attempts.pop(key, None)

        log.error(
            "sent offset %s of partition %s to %s after %s attempts: %s",
            msg.offset(),
            msg.partition(),
            self._dlt_topic,
            MAX_ATTEMPTS,
            error,
        )

    def forget(self, msg) -> None:
        """Drop the counter for a message that finally succeeded."""
        self._attempts.pop((msg.partition(), msg.offset()), None)

    def close(self) -> None:
        self._producer.flush(10)