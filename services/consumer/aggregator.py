"""Hourly aggregation consumer.

Reads measurement events from Kafka and recomputes the hourly aggregate for the
affected node and hour (mapping 1: Measurement -> HourlyAggregate).

Delivery is at-least-once, so the same event can arrive more than once. Two
mechanisms handle that: the aggregate is recomputed from scratch rather than
incremented, which makes the work itself idempotent, and processed message ids
are recorded so repeated work is skipped (NFR-6).
"""

import json
import logging
import os
import signal
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import time

from confluent_kafka import Consumer, KafkaError, TopicPartition
from poison import PoisonHandler
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://gas:gas@127.0.0.1:5434/gas_metering"
)
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:29092")
TOPIC = os.getenv("TOPIC", "measurements.recorded")
GROUP_ID = os.getenv("GROUP_ID", "hourly-aggregator")
CONSUMER_NAME = "hourly-aggregator"
# Pause between retries so a transient failure has time to clear.
RETRY_DELAY = 2.0
DLT_TOPIC = os.getenv("DLT_TOPIC", "measurements.dlt")

# NFR-9: one measurement per minute, so a complete hour holds sixty of them.
MEASUREMENTS_PER_HOUR = 60

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(CONSUMER_NAME)

running = True


def stop(signum, frame):
    global running
    log.info("shutdown requested")
    running = False


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)


def already_processed(conn, message_key: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM processed_message WHERE consumer = %s AND message_key = %s",
        (CONSUMER_NAME, message_key),
    ).fetchone()
    return row is not None


def recompute_hour(conn, node_id: str, measured_at: str) -> None:
    """Rebuild the aggregate for the hour containing measured_at.

    Recomputing the whole hour rather than adding to a running total keeps the
    operation idempotent and lets late archive data (FR-16) correct an hour that
    was already published.
    """
    conn.execute(
        """
        INSERT INTO hourly_aggregate (
            id, node_id, hour_start, volume,
            avg_pressure, avg_temperature, measurement_count, is_complete
        )
        SELECT
            gen_random_uuid(),
            m.node_id,
            date_trunc('hour', %(measured_at)s::timestamptz),
            sum(m.flow_rate) / 60,
            avg(m.pressure),
            avg(m.temperature),
            count(*),
            count(*) >= %(expected)s
        FROM measurement m
        WHERE m.node_id = %(node_id)s
          AND m.quality = 'valid'
          AND m.measured_at >= date_trunc('hour', %(measured_at)s::timestamptz)
          AND m.measured_at <  date_trunc('hour', %(measured_at)s::timestamptz)
                               + interval '1 hour'
        GROUP BY m.node_id
        ON CONFLICT (node_id, hour_start) DO UPDATE SET
            volume            = excluded.volume,
            avg_pressure      = excluded.avg_pressure,
            avg_temperature   = excluded.avg_temperature,
            measurement_count = excluded.measurement_count,
            is_complete       = excluded.is_complete,
            computed_at       = now()
        """,
        {
            "node_id": node_id,
            "measured_at": measured_at,
            "expected": MEASUREMENTS_PER_HOUR,
        },
    )

def correlation_of(msg) -> str:
    """Pull the correlation id out of the Kafka headers."""
    for name, value in msg.headers() or []:
        if name == "correlation_id" and value:
            return value.decode()
    return "-"

def handle(conn, event: dict) -> bool:
    message_key = event["measurement_id"]

    if already_processed(conn, message_key):
        log.info("skipping duplicate measurement %s", message_key)
        return False

    recompute_hour(conn, event["node_id"], event["measured_at"])

    conn.execute(
        "INSERT INTO processed_message (consumer, message_key) VALUES (%s, %s)",
        (CONSUMER_NAME, message_key),
    )
    return True


def main() -> None:
    pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=2, open=True)

    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP,
            "group.id": GROUP_ID,
            # Start from the beginning when the group has no stored offset.
            "auto.offset.reset": "earliest",
            # Offsets are committed by hand, after the work is durable.
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([TOPIC])
    poison = PoisonHandler(KAFKA_BOOTSTRAP, DLT_TOPIC, CONSUMER_NAME)
    log.info("consumer started, topic=%s group=%s", TOPIC, GROUP_ID)

    while running:
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            if msg.error().code() != KafkaError._PARTITION_EOF:
                log.error("consume error: %s", msg.error())
            continue

        try:
            event = json.loads(msg.value())
            correlation_id = correlation_of(msg)
            with pool.connection() as conn:
                conn.row_factory = dict_row
                with conn.transaction():
                    processed = handle(conn, event)

            poison.forget(msg)
            consumer.commit(msg)

            if processed:
                log.info(
                    "aggregated node=%s measured_at=%s partition=%s offset=%s cid=%s",
                    event["node_code"],
                    event["measured_at"],
                    msg.partition(),
                    msg.offset(),
                    correlation_id,
                )
        except Exception as exc:
            if poison.should_retry(msg):
                log.warning(
                    "failed to handle offset %s, will retry: %s", msg.offset(), exc
                )
                # poll() would hand over the next message, so rewind the
                # partition to this offset to actually retry the same one.
                consumer.seek(
                    TopicPartition(msg.topic(), msg.partition(), msg.offset())
                )
                time.sleep(RETRY_DELAY)
                continue
            # Out of retries: park the message and move the partition forward,
            # otherwise everything behind it stops too.
            poison.send_to_dlt(msg, str(exc))
            consumer.commit(msg)
    poison.close()
    consumer.close()
    pool.close()
    log.info("consumer stopped")


if __name__ == "__main__":
    main()
