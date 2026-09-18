"""Gas day boundaries.

The gas day runs 10:00 to 10:00, not midnight to midnight, so a measurement
taken before 10:00 belongs to the gas day that started the previous calendar
day. Getting this wrong silently attributes volumes to the wrong day, which is
exactly the kind of error a reconciliation system exists to prevent.
"""

from datetime import datetime, timezone

from deviation_detector import gas_day_bounds


def utc(year, month, day, hour, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def test_measurement_after_start_belongs_to_same_calendar_day():
    start, end = gas_day_bounds(utc(2026, 9, 17, 14))
    assert start == utc(2026, 9, 17, 10)
    assert end == utc(2026, 9, 18, 10)


def test_measurement_before_start_belongs_to_previous_gas_day():
    start, end = gas_day_bounds(utc(2026, 9, 17, 9, 59))
    assert start == utc(2026, 9, 16, 10)
    assert end == utc(2026, 9, 17, 10)


def test_exact_start_opens_a_new_gas_day():
    start, _ = gas_day_bounds(utc(2026, 9, 17, 10))
    assert start == utc(2026, 9, 17, 10)


def test_last_minute_before_start_still_belongs_to_the_old_day():
    start, end = gas_day_bounds(utc(2026, 9, 17, 9, 59))
    assert end == utc(2026, 9, 17, 10)
    assert start < utc(2026, 9, 17, 0)