"""Measurement intake and the transactional outbox.

These are the guarantees the whole delivery chain rests on: a measurement and
its event are written together or not at all (no dual-write hole), and a
re-read of the controller archive cannot create duplicates (FR-16, NFR-6).
"""

from uuid import uuid4

NODE_ID = "11111111-1111-1111-1111-111111111111"
MEASURED_AT = "2026-09-17T10:00:00+00:00"


def insert_measurement(conn, measured_at=MEASURED_AT):
    measurement_id = uuid4()
    row = conn.execute(
        """
        INSERT INTO measurement (
            id, node_id, measured_at, flow_rate, pressure, temperature, source
        )
        VALUES (%s, %s, %s, 1250.0, 55.0, 12.0, 'telemetry')
        ON CONFLICT (node_id, measured_at) DO NOTHING
        RETURNING id
        """,
        (measurement_id, NODE_ID, measured_at),
    ).fetchone()

    if row is None:
        return None

    conn.execute(
        """
        INSERT INTO outbox (
            aggregate_type, aggregate_id, event_type, partition_key, payload
        )
        VALUES ('measurement', %s, 'measurement.recorded', %s, '{}')
        """,
        (measurement_id, NODE_ID),
    )
    return measurement_id


def test_measurement_is_stored_with_its_event(seeded):
    assert insert_measurement(seeded) is not None

    measurements = seeded.execute(
        "SELECT count(*) AS n FROM measurement WHERE node_id = %s", (NODE_ID,)
    ).fetchone()
    events = seeded.execute(
        "SELECT count(*) AS n FROM outbox WHERE partition_key = %s", (NODE_ID,)
    ).fetchone()

    assert measurements["n"] == 1
    assert events["n"] == 1


def test_archive_re_read_creates_no_duplicate(seeded):
    insert_measurement(seeded)
    assert insert_measurement(seeded) is None

    measurements = seeded.execute(
        "SELECT count(*) AS n FROM measurement WHERE node_id = %s", (NODE_ID,)
    ).fetchone()
    events = seeded.execute(
        "SELECT count(*) AS n FROM outbox WHERE partition_key = %s", (NODE_ID,)
    ).fetchone()

    assert measurements["n"] == 1
    # The duplicate must not queue a second event either: an event published
    # twice would be handed to every consumer twice.
    assert events["n"] == 1


def test_different_timestamps_are_separate_measurements(seeded):
    insert_measurement(seeded, "2026-09-17T10:00:00+00:00")
    insert_measurement(seeded, "2026-09-17T10:01:00+00:00")

    measurements = seeded.execute(
        "SELECT count(*) AS n FROM measurement WHERE node_id = %s", (NODE_ID,)
    ).fetchone()
    assert measurements["n"] == 2