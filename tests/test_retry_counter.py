"""Retry counting for RabbitMQ.

The x-death header carries one entry per queue a message has died in, and a
single retry cycle touches two of them: the work queue on rejection and the
retry queue on TTL expiry. Summing every entry therefore double-counts and
halves the effective retry budget — a bug that shipped and was only visible
because the attempt numbers in the log jumped by two.
"""

from types import SimpleNamespace

from notifier import QUEUE_SEND, death_count


def properties(headers):
    return SimpleNamespace(headers=headers)


def test_no_header_means_no_previous_death():
    assert death_count(properties(None)) == 0


def test_counts_only_the_work_queue():
    props = properties(
        {
            "x-death": [
                {"queue": QUEUE_SEND, "count": 3},
                {"queue": "notifications.retry", "count": 3},
            ]
        }
    )
    assert death_count(props) == 3


def test_unknown_queues_are_ignored():
    props = properties({"x-death": [{"queue": "notifications.retry", "count": 7}]})
    assert death_count(props) == 0
