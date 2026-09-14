"""Notification worker.

Consumes notification commands from RabbitMQ and delivers them to the
counterparty (FR-22, NFR-5). Sending is simulated: the point of this service is
the delivery guarantees around it, not the transport itself.

Failure handling: a failed attempt is rejected without requeue, which routes the
message to the retry queue, where it waits out a TTL before returning here.
After the retry budget is spent the message is routed to the dead letter queue
for manual handling, mirroring the suspect-packet queue in FR-08.
"""

import json
import logging
import os
import random
import signal

import pika
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://gas:gas@127.0.0.1:5434/gas_metering"
)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://gas:gas@127.0.0.1:5672/")
EXCHANGE = "notifications"
QUEUE_SEND = "notifications.send"
ROUTING_KEY_DEAD = "notification.dead"

MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "5"))
# Probability that a simulated send fails, so retries can be observed.
FAILURE_RATE = float(os.getenv("FAILURE_RATE", "0.0"))
# One unacknowledged message at a time: without this the broker hands the
# worker everything at once and a slow consumer hoards messages others could
# be processing.
PREFETCH = 1

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("pika").setLevel(logging.WARNING)
log = logging.getLogger("notifier")

def death_count(properties) -> int:
    """How many times this message has been dead-lettered from the work queue.

    The x-death header holds one entry per queue a message has died in, and a
    single retry cycle touches two of them: the work queue on rejection and the
    retry queue on TTL expiry. Summing every entry therefore double-counts, so
    only the work queue is consulted.
    """
    headers = properties.headers or {}
    for entry in headers.get("x-death") or []:
        if entry.get("queue") == QUEUE_SEND:
            return entry.get("count", 0)
    return 0

def send_notification(payload: dict) -> None:
    """Stand-in for the real email or SMS gateway."""
    if random.random() < FAILURE_RATE:
        raise RuntimeError("notification gateway unavailable")
    log.info(
        "sent %s to %s for delivery point %s (%.2f%%)",
        payload["channel"],
        payload["address"],
        payload["delivery_point_code"],
        payload["deviation_pct"],
    )


def mark_notification(pool, deviation_id: str, status: str, attempts: int, error=None):
    with pool.connection() as conn:
        conn.row_factory = dict_row
        conn.execute(
            """
            INSERT INTO notification (
                id, deviation_id, channel, recipient, status, attempts,
                last_error, sent_at
            )
            SELECT gen_random_uuid(), d.id, dp.notify_channel, dp.notify_address,
                    %(status)s::notification_status, %(attempts)s, %(error)s,
                    CASE WHEN %(status)s::text = 'sent' THEN now() END
            FROM deviation d
            JOIN delivery_point dp ON dp.id = d.delivery_point_id
            WHERE d.id = %(deviation_id)s
            """,
            {
                "deviation_id": deviation_id,
                "status": status,
                "attempts": attempts,
                "error": error,
            },
        )


def main() -> None:
    pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=2, open=True)
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()
    channel.basic_qos(prefetch_count=PREFETCH)

    def on_message(ch, method, properties, body):
        payload = json.loads(body)
        deviation_id = payload["deviation_id"]
        attempts = death_count(properties) + 1

        try:
            send_notification(payload)
        except Exception as exc:
            if attempts >= MAX_ATTEMPTS:
                log.error(
                    "giving up on deviation %s after %s attempts, routing to DLQ",
                    deviation_id,
                    attempts,
                )
                mark_notification(pool, deviation_id, "dead", attempts, str(exc))
                ch.basic_publish(
                    exchange=EXCHANGE,
                    routing_key=ROUTING_KEY_DEAD,
                    body=body,
                    properties=properties,
                )
                ch.basic_ack(method.delivery_tag)
            else:
                log.warning(
                    "attempt %s/%s failed for deviation %s: %s",
                    attempts,
                    MAX_ATTEMPTS,
                    deviation_id,
                    exc,
                )
                # Reject without requeue: the dead-letter settings on this queue
                # send the message to the retry queue, not back here directly.
                ch.basic_nack(method.delivery_tag, requeue=False)
            return

        mark_notification(pool, deviation_id, "sent", attempts)
        ch.basic_ack(method.delivery_tag)

    channel.basic_consume(queue=QUEUE_SEND, on_message_callback=on_message)

    def stop(signum, frame):
        log.info("shutdown requested")
        channel.stop_consuming()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    log.info("worker started, queue=%s max_attempts=%s", QUEUE_SEND, MAX_ATTEMPTS)
    channel.start_consuming()

    connection.close()
    pool.close()
    log.info("worker stopped")


if __name__ == "__main__":
    main()