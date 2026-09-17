"""Outbox relay.

Delivers rows written by the API and the consumers to their broker. Events go
to Kafka, commands go to RabbitMQ; the destination column decides which.

Delivery is at-least-once in both directions: a crash between a successful send
and the local mark can republish a row, which receivers must tolerate (NFR-6).
"""

import json
import logging
import os
import signal
import time

import pika
from confluent_kafka import Producer
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://gas:gas@127.0.0.1:5434/gas_metering"
)
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:29092")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://gas:gas@127.0.0.1:5672/")
TOPIC = os.getenv("TOPIC", "measurements.recorded")
EXCHANGE = os.getenv("EXCHANGE", "notifications")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "1.0"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("relay")

running = True


def stop(signum, frame):
    global running
    log.info("shutdown requested")
    running = False


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)


def build_producer() -> Producer:
    return Producer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP,
            "acks": "all",
            "retries": 10,
            "retry.backoff.ms": 200,
            "enable.idempotence": True,
            "linger.ms": 20,
        }
    )


class RabbitChannel:
    """Lazily opened RabbitMQ channel with publisher confirms.

    Confirms matter here for the same reason acks=all matters for Kafka: without
    them publish returns as soon as the bytes leave the process, and a row would
    be marked published before the broker ever stored it.
    """

    def __init__(self, url: str):
        self._url = url
        self._connection = None
        self._channel = None

    def channel(self):
        if self._connection is None or self._connection.is_closed:
            self._connection = pika.BlockingConnection(pika.URLParameters(self._url))
            self._channel = self._connection.channel()
            self._channel.confirm_delivery()
        return self._channel

    def close(self):
        if self._connection is not None and self._connection.is_open:
            self._connection.close()


def publish_kafka(rows, producer: Producer):
    delivered, failed = [], []

    def on_delivery(err, msg, row_id):
        if err is None:
            delivered.append(row_id)
        else:
            failed.append((str(err), row_id))

    for row in rows:
        producer.produce(
            topic=TOPIC,
            key=row["partition_key"].encode(),
            value=json.dumps(row["payload"]).encode(),
            headers=[
                ("event_type", row["event_type"]),
                ("correlation_id", str(row["correlation_id"] or "")),
            ],
            on_delivery=lambda err, msg, row_id=row["id"]: on_delivery(err, msg, row_id),
        )

    producer.flush(30)
    return delivered, failed


def publish_rabbit(rows, rabbit: RabbitChannel):
    delivered, failed = [], []
    channel = rabbit.channel()

    for row in rows:
        try:
            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=row["routing_key"],
                body=json.dumps(row["payload"]).encode(),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    correlation_id=str(row["correlation_id"] or ""),
                    # Persist the message to disk so a broker restart does not
                    # empty a durable queue.
                    delivery_mode=2,
                    message_id=str(row["aggregate_id"]),
                    type=row["event_type"],
                ),
            )
            delivered.append(row["id"])
        except Exception as exc:
            failed.append((str(exc), row["id"]))

    return delivered, failed


def publish_batch(conn, producer: Producer, rabbit: RabbitChannel) -> int:
    rows = conn.execute(
        """
        SELECT id, aggregate_id, event_type, destination,
            partition_key, routing_key, payload, correlation_id
        FROM outbox
        WHERE published_at IS NULL
        ORDER BY id
        LIMIT %s
        FOR UPDATE SKIP LOCKED
        """,
        (BATCH_SIZE,),
    ).fetchall()

    if not rows:
        return 0

    kafka_rows = [r for r in rows if r["destination"] == "kafka"]
    rabbit_rows = [r for r in rows if r["destination"] == "rabbitmq"]

    delivered, failed = [], []

    if kafka_rows:
        d, f = publish_kafka(kafka_rows, producer)
        delivered += d
        failed += f

    if rabbit_rows:
        d, f = publish_rabbit(rabbit_rows, rabbit)
        delivered += d
        failed += f

    if delivered:
        conn.execute(
            "UPDATE outbox SET published_at = now() WHERE id = ANY(%s)",
            (delivered,),
        )

    for error, row_id in failed:
        log.error("delivery failed for outbox row %s: %s", row_id, error)
        conn.execute(
            "UPDATE outbox SET attempts = attempts + 1, last_error = %s WHERE id = %s",
            (error, row_id),
        )

    return len(delivered)


def main() -> None:
    pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=2, open=True)
    producer = build_producer()
    rabbit = RabbitChannel(RABBITMQ_URL)
    log.info("relay started, kafka=%s rabbitmq=%s", KAFKA_BOOTSTRAP, EXCHANGE)

    while running:
        try:
            with pool.connection() as conn:
                conn.row_factory = dict_row
                with conn.transaction():
                    sent = publish_batch(conn, producer, rabbit)
            if sent:
                log.info("published %s rows", sent)
            else:
                time.sleep(POLL_INTERVAL)
        except Exception:
            log.exception("relay iteration failed")
            time.sleep(POLL_INTERVAL)

    producer.flush(10)
    rabbit.close()
    pool.close()
    log.info("relay stopped")


if __name__ == "__main__":
    main()