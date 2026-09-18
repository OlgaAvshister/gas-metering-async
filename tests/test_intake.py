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
            id, node_id, measured_at, volume_raw, pressure, temperature, source
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


def test_only_one_contract_parameter_is_in_force_per_delivery_point(seeded):
    """The ER model states this but calls it unenforceable in the schema.

    For a single open interval it is enforceable, and a partial unique index
    does it — so a second open row is rejected by the database rather than by
    whichever service happens to check.
    """
    import psycopg
    import pytest

    point_id = seeded.execute(
        "SELECT id FROM delivery_point ORDER BY code LIMIT 1"
    ).fetchone()["id"]

    with pytest.raises(psycopg.errors.UniqueViolation):
        seeded.execute(
            """
            INSERT INTO contract_parameter (
                id, delivery_point_id, valid_from, valid_to,
                daily_nomination, deviation_threshold,
                accumulated_deviation_threshold
            )
            VALUES (gen_random_uuid(), %s, now(), NULL, 30000, 5.00, 2.00)
            """,
            (point_id,),
        )
