"""Outbox relay.

Publishes events recorded by the intake API to Kafka. The API writes the
business row and its event in one transaction; this process delivers them.
Delivery is at-least-once: a crash between a successful send and the local
mark can republish an event, which consumers must tolerate (NFR-6).
"""

import json
import logging
import os
import signal
import time

from confluent_kafka import Producer
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://gas:gas@127.0.0.1:5434/gas_metering"
)
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:29092")
TOPIC = os.getenv("TOPIC", "measurements.recorded")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "1.0"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
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
            # Wait for all in-sync replicas before considering a write durable.
            "acks": "all",
            # Retry transient broker errors instead of losing the event.
            "retries": 10,
            "retry.backoff.ms": 200,
            # Guarantees no duplicates and preserved order within a partition
            # for retries inside a single producer session.
            "enable.idempotence": True,
            "linger.ms": 20,
        }
    )


def publish_batch(conn, producer: Producer) -> int:
    rows = conn.execute(
        """
        SELECT id, event_type, partition_key, payload
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

    delivered: list[int] = []
    failed: list[tuple[str, int]] = []

    def on_delivery(err, msg, row_id=None):
        if err is None:
            delivered.append(row_id)
        else:
            failed.append((str(err), row_id))

    for row in rows:
        producer.produce(
            topic=TOPIC,
            key=row["partition_key"].encode(),
            value=json.dumps(row["payload"]).encode(),
            headers=[("event_type", row["event_type"])],
            on_delivery=lambda err, msg, row_id=row["id"]: on_delivery(
                err, msg, row_id
            ),
        )

    producer.flush(30)

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
    log.info("relay started, topic=%s bootstrap=%s", TOPIC, KAFKA_BOOTSTRAP)

    while running:
        try:
            with pool.connection() as conn:
                conn.row_factory = dict_row
                with conn.transaction():
                    sent = publish_batch(conn, producer)
            if sent:
                log.info("published %s events", sent)
            else:
                time.sleep(POLL_INTERVAL)
        except Exception:
            log.exception("relay iteration failed")
            time.sleep(POLL_INTERVAL)

    producer.flush(10)
    pool.close()
    log.info("relay stopped")


if __name__ == "__main__":
    main()