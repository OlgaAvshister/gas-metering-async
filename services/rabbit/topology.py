"""Declares the RabbitMQ topology.

Kept as code rather than clicks in the management UI so the topology is
versioned and reproducible. Safe to run repeatedly: declarations are
idempotent as long as the arguments do not change.
"""

import logging
import os

import pika

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://gas:gas@127.0.0.1:5672/")

EXCHANGE = "notifications"
QUEUE_SEND = "notifications.send"
QUEUE_RETRY = "notifications.retry"
QUEUE_DLQ = "notifications.dlq"
ROUTING_KEY_SEND = "notification.send"

# NFR-5 allows three minutes end to end, so retries have to stay short.
RETRY_DELAY_MS = 30_000

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("topology")


def declare() -> None:
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()

    channel.exchange_declare(
        exchange=EXCHANGE, exchange_type="topic", durable=True
    )

    # Working queue. A failed message is rejected without requeue, which sends
    # it to the retry queue through this queue's dead-letter settings.
    channel.queue_declare(
        queue=QUEUE_SEND,
        durable=True,
        arguments={
            "x-dead-letter-exchange": EXCHANGE,
            "x-dead-letter-routing-key": "notification.retry",
        },
    )
    channel.queue_bind(
        queue=QUEUE_SEND, exchange=EXCHANGE, routing_key=ROUTING_KEY_SEND
    )

    # Retry queue. Nothing consumes from it: messages sit here until the TTL
    # expires and the dead-letter settings route them back to the working queue.
    channel.queue_declare(
        queue=QUEUE_RETRY,
        durable=True,
        arguments={
            "x-message-ttl": RETRY_DELAY_MS,
            "x-dead-letter-exchange": EXCHANGE,
            "x-dead-letter-routing-key": ROUTING_KEY_SEND,
        },
    )
    channel.queue_bind(
        queue=QUEUE_RETRY, exchange=EXCHANGE, routing_key="notification.retry"
    )

    # Dead letter queue. Terminal: a message here has exhausted its retries and
    # waits for a human, mirroring the manual review queue in FR-08.
    channel.queue_declare(queue=QUEUE_DLQ, durable=True)
    channel.queue_bind(
        queue=QUEUE_DLQ, exchange=EXCHANGE, routing_key="notification.dead"
    )

    log.info("topology declared on %s", EXCHANGE)
    connection.close()


if __name__ == "__main__":
    declare()
