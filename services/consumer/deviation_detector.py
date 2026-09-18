"""Deviation detection consumer.

Compares incoming measurements against the contractual nomination (FR-07) and,
when the accumulated deviation crosses the agreed threshold, queues a
counterparty notification (FR-22, NFR-5) through the transactional outbox.

Two comparisons are made, per UC-01: the instantaneous flow against the hourly
share of the plan, and the volume accumulated since the start of the gas day
against the plan pro-rated to the current moment.

The planned value is never stored on the deviation. The row records which
ContractParameter version it was judged against, and the plan is derived from
that, so the two cannot drift apart when a nomination changes.
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from confluent_kafka import Consumer, KafkaError, TopicPartition
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from poison import PoisonHandler  # noqa: E402

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://gas:gas@127.0.0.1:5434/gas_metering"
)
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:29092")
TOPIC = os.getenv("TOPIC", "measurements.recorded")
DLT_TOPIC = os.getenv("DLT_TOPIC", "measurements.dlt")
GROUP_ID = os.getenv("GROUP_ID", "deviation-detector")
CONSUMER_NAME = "deviation-detector"

# Gas day runs 10:00 to 10:00 UTC, not midnight to midnight (see glossary).
GAS_DAY_START_HOUR = 10
RETRY_DELAY = 2.0

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(CONSUMER_NAME)

running = True


def stop(signum, frame):
    global running
    log.info("shutdown requested")
    running = False


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)


def correlation_of(msg) -> str:
    for name, value in msg.headers() or []:
        if name == "correlation_id" and value:
            return value.decode()
    return "-"


def gas_day_bounds(measured_at: datetime) -> tuple[datetime, datetime]:
    """Return the start and end of the gas day containing measured_at."""
    start = measured_at.replace(
        hour=GAS_DAY_START_HOUR, minute=0, second=0, microsecond=0
    )
    if measured_at < start:
        start -= timedelta(days=1)
    return start, start + timedelta(days=1)


def find_contract_parameter(conn, node_id: str, at: datetime):
    """The contract parameters in force for this node at this moment.

    Validity is an interval, so a nomination that changed mid-period does not
    retroactively re-judge earlier measurements.
    """
    return conn.execute(
        """
        SELECT cp.id, cp.delivery_point_id, cp.daily_nomination,
               cp.deviation_threshold, cp.accumulated_deviation_threshold
        FROM contract_parameter cp
        JOIN node_delivery_link l ON l.delivery_point_id = cp.delivery_point_id
        WHERE l.node_id = %s
          AND cp.valid_from <= %s
          AND (cp.valid_to IS NULL OR cp.valid_to > %s)
        """,
        (node_id, at, at),
    ).fetchone()


def accumulated_volume(conn, node_id: str, start: datetime, until: datetime) -> float:
    """Volume delivered since the start of the gas day.

    Readings are instantaneous flow per hour taken once a minute, so each
    contributes a sixtieth of an hour's worth.
    """
    row = conn.execute(
        """
        SELECT coalesce(sum(volume_raw), 0) / 60 AS volume
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
    conn, kind, node_id, parameter, measured_at, planned, actual, correlation_id
):
    deviation_id = uuid4()
    deviation_value = (actual - planned) / planned * 100 if planned else 0
    threshold = (
        parameter["deviation_threshold"]
        if kind == "instantaneous"
        else parameter["accumulated_deviation_threshold"]
    )

    conn.execute(
        """
        INSERT INTO deviation (
            id, node_id, delivery_point_id, contract_parameter_id, measured_at,
            actual_value, deviation_value, threshold_value, kind, correlation_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            deviation_id,
            node_id,
            parameter["delivery_point_id"],
            parameter["id"],
            measured_at,
            actual,
            deviation_value,
            threshold,
            kind,
            correlation_id,
        ),
    )
    return deviation_id, deviation_value


def queue_notification(
    conn, deviation_id, parameter, deviation_value, measured_at, correlation_id
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
        (parameter["delivery_point_id"],),
    ).fetchone()

    payload = {
        "deviation_id": str(deviation_id),
        "delivery_point_code": point["code"],
        "counterparty": point["counterparty_name"],
        "channel": point["notify_channel"],
        "address": point["notify_address"],
        "deviation_value": round(deviation_value, 2),
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
            str(parameter["delivery_point_id"]),
            "notification.send",
            "rabbitmq",
            json.dumps(payload),
            correlation_id,
        ),
    )


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

    parameter = find_contract_parameter(conn, node_id, measured_at)
    if parameter is None:
        log.warning("no contract parameters for node %s at %s", node_id, measured_at)
        return

    planned_total = float(parameter["daily_nomination"])

    # Instantaneous: flow against the hourly share of the daily plan.
    planned_hourly = planned_total / 24
    actual_rate = float(event["volume_raw"])
    instant_pct = abs(actual_rate - planned_hourly) / planned_hourly * 100

    if instant_pct > float(parameter["deviation_threshold"]):
        record_deviation(
            conn, "instantaneous", node_id, parameter,
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

    if accumulated_pct <= float(parameter["accumulated_deviation_threshold"]):
        return

    # One notification per open deviation: without this the counterparty gets a
    # message on every measurement while the flow hovers around the threshold.
    if has_open_accumulated_deviation(conn, parameter["delivery_point_id"], start, end):
        log.info("accumulated deviation already open, no new notification")
        return

    deviation_id, value = record_deviation(
        conn, "accumulated", node_id, parameter,
        measured_at, planned_so_far, actual_so_far, correlation_id,
    )
    queue_notification(
        conn, deviation_id, parameter, value, event["measured_at"], correlation_id
    )
    log.info("accumulated deviation %.2f%%, notification queued", value)


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
                    handle(conn, event, correlation_id)
            poison.forget(msg)
            consumer.commit(msg)
        except Exception as exc:
            if poison.should_retry(msg):
                log.warning(
                    "failed to handle offset %s, will retry: %s", msg.offset(), exc
                )
                consumer.seek(
                    TopicPartition(msg.topic(), msg.partition(), msg.offset())
                )
                time.sleep(RETRY_DELAY)
                continue
            poison.send_to_dlt(msg, str(exc))
            consumer.commit(msg)

    poison.close()
    consumer.close()
    pool.close()
    log.info("consumer stopped")


if __name__ == "__main__":
    main()
