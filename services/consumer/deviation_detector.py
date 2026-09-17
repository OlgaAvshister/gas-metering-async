"""Deviation detection consumer.

Compares incoming measurements against the daily nomination (FR-07) and, when
the accumulated deviation crosses the contractual threshold, queues a
counterparty notification (FR-22, NFR-5) through the transactional outbox.

Two comparisons are made, per UC-01: the instantaneous flow rate against the
hourly share of the plan, and the volume accumulated since the start of the gas
day against the plan pro-rated to the current moment.
"""

import json
import logging
import os
import signal
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from confluent_kafka import Consumer, KafkaError
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://gas:gas@127.0.0.1:5434/gas_metering"
)
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:29092")
TOPIC = os.getenv("TOPIC", "measurements.recorded")
GROUP_ID = os.getenv("GROUP_ID", "deviation-detector")
CONSUMER_NAME = "deviation-detector"

# Gas day runs 10:00 to 10:00 UTC, not midnight to midnight (see glossary).
GAS_DAY_START_HOUR = 10

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(CONSUMER_NAME)

running = True


def stop(signum, frame):
    global running
    log.info("shutdown requested")
    running = False


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)


def gas_day_bounds(measured_at: datetime) -> tuple[datetime, datetime]:
    """Return the start and end of the gas day containing measured_at."""
    start = measured_at.replace(
        hour=GAS_DAY_START_HOUR, minute=0, second=0, microsecond=0
    )
    if measured_at < start:
        start -= timedelta(days=1)
    return start, start + timedelta(days=1)


def find_nomination(conn, node_id: str, gas_day_start: datetime):
    return conn.execute(
        """
        SELECT n.id, n.delivery_point_id, n.planned_volume,
               n.threshold_pct, n.accumulated_threshold_pct
        FROM nomination n
        JOIN node_delivery_link l ON l.delivery_point_id = n.delivery_point_id
        WHERE l.node_id = %s AND n.gas_day = %s::date
        """,
        (node_id, gas_day_start.date()),
    ).fetchone()


def accumulated_volume(conn, node_id: str, start: datetime, until: datetime) -> float:
    row = conn.execute(
        """
        SELECT coalesce(sum(flow_rate), 0) / 60 AS volume
        FROM measurement
        WHERE node_id = %s
          AND quality = 'valid'
          AND measured_at >= %s
          AND measured_at <= %s
        """,
        (node_id, start, until),
    ).fetchone()
    return float(row["volume"])


def has_open_accumulated_deviation(conn, delivery_point_id, start, end) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM deviation
        WHERE delivery_point_id = %s
          AND kind = 'accumulated'
          AND status = 'open'
          AND measured_at >= %s AND measured_at < %s
        LIMIT 1
        """,
        (delivery_point_id, start, end),
    ).fetchone()
    return row is not None


def record_deviation(
    conn, kind, node_id, nomination, measured_at, planned, actual, correlation_id
):
    deviation_id = uuid4()
    deviation_pct = (actual - planned) / planned * 100 if planned else 0
    threshold = (
        nomination["threshold_pct"]
        if kind == "instantaneous"
        else nomination["accumulated_threshold_pct"]
    )

    conn.execute(
        """
        INSERT INTO deviation (
            id, node_id, delivery_point_id, measured_at,
            nominated_value, actual_value, deviation_pct, threshold_pct, kind,
            correlation_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            deviation_id,
            node_id,
            nomination["delivery_point_id"],
            measured_at,
            planned,
            actual,
            deviation_pct,
            threshold,
            kind,
            correlation_id,
        ),
    )
    return deviation_id, deviation_pct


def queue_notification(
    conn, deviation_id, nomination, deviation_pct, measured_at, correlation_id
):
    """Write the notification command to the outbox in the same transaction.

    The deviation row and the command are committed together; the relay
    publishes the command to RabbitMQ afterwards.
    """
    point = conn.execute(
        """
        SELECT code, counterparty_name, notify_channel, notify_address
        FROM delivery_point WHERE id = %s
        """,
        (nomination["delivery_point_id"],),
    ).fetchone()

    payload = {
        "deviation_id": str(deviation_id),
        "delivery_point_code": point["code"],
        "counterparty": point["counterparty_name"],
        "channel": point["notify_channel"],
        "address": point["notify_address"],
        "deviation_pct": round(deviation_pct, 2),
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "measured_at": measured_at,
    }

    conn.execute(
        """
        INSERT INTO outbox (
            aggregate_type, aggregate_id, event_type,
            partition_key, routing_key, destination, payload, correlation_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            "deviation",
            deviation_id,
            "notification.send",
            str(nomination["delivery_point_id"]),
            "notification.send",
            "rabbitmq",
            json.dumps(payload),
            correlation_id,
        ),
    )

def correlation_of(msg) -> str:
    """Pull the correlation id out of the Kafka headers."""
    for name, value in msg.headers() or []:
        if name == "correlation_id" and value:
            return value.decode()
    return "-"

def handle(conn, event: dict, correlation_id: str) -> None:
    message_key = event["measurement_id"]

    row = conn.execute(
        "SELECT 1 FROM processed_message WHERE consumer = %s AND message_key = %s",
        (CONSUMER_NAME, message_key),
    ).fetchone()
    if row is not None:
        log.info("skipping duplicate measurement %s", message_key)
        return

    conn.execute(
        "INSERT INTO processed_message (consumer, message_key) VALUES (%s, %s)",
        (CONSUMER_NAME, message_key),
    )

    node_id = event["node_id"]
    measured_at = datetime.fromisoformat(event["measured_at"])
    start, end = gas_day_bounds(measured_at)

    nomination = find_nomination(conn, node_id, start)
    if nomination is None:
        log.warning("no nomination for node %s on gas day %s", node_id, start.date())
        return

    planned_total = float(nomination["planned_volume"])

    # Instantaneous: flow rate against the hourly share of the daily plan.
    planned_hourly = planned_total / 24
    actual_rate = float(event["flow_rate"])
    instant_pct = abs(actual_rate - planned_hourly) / planned_hourly * 100

    if instant_pct > float(nomination["threshold_pct"]):
        record_deviation(
            conn, "instantaneous", node_id, nomination,
            measured_at, planned_hourly, actual_rate, correlation_id,
        )
        log.info("instantaneous deviation %.2f%% on node %s", instant_pct, node_id)

    # Accumulated: volume since the start of the gas day against the plan
    # pro-rated to this point in the day. The linear profile is a
    # simplification; a real contract carries an hourly delivery curve.
    elapsed_hours = (measured_at - start).total_seconds() / 3600
    if elapsed_hours <= 0:
        return

    planned_so_far = planned_total * elapsed_hours / 24
    actual_so_far = accumulated_volume(conn, node_id, start, measured_at)
    accumulated_pct = abs(actual_so_far - planned_so_far) / planned_so_far * 100

    if accumulated_pct <= float(nomination["accumulated_threshold_pct"]):
        return

    # One notification per open deviation: without this the counterparty gets a
    # message on every measurement while the flow hovers around the threshold.
    if has_open_accumulated_deviation(conn, nomination["delivery_point_id"], start, end):
        log.info("accumulated deviation already open, no new notification")
        return

    deviation_id, pct = record_deviation(
        conn, "accumulated", node_id, nomination,
        measured_at, planned_so_far, actual_so_far, correlation_id,
    )
    queue_notification(
        conn, deviation_id, nomination, pct, event["measured_at"], correlation_id
    )
    log.info("accumulated deviation %.2f%%, notification queued", pct)


def main() -> None:
    pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=2, open=True)
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP,
            "group.id": GROUP_ID,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([TOPIC])
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
                    handle(conn, event, correlation_id)
            consumer.commit(msg)
        except Exception:
            log.exception("failed to handle offset %s, not committing", msg.offset())

    consumer.close()
    pool.close()
    log.info("consumer stopped")


if __name__ == "__main__":
    main()