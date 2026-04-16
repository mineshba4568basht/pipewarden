"""Tests for pipewarden.deduplication."""
from datetime import datetime, timedelta

import pytest

from pipewarden.config import AlertRule
from pipewarden.runner import AlertEvent
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.deduplication import DeduplicationFilter, DedupeRecord


def _make_event(pipeline: str = "pipe_a", check: str = "row_count") -> AlertEvent:
    rule = AlertRule(check_name=check, threshold=10)
    result = CheckResult(check_name=check, status=CheckStatus.FAIL, value=0, threshold=10)
    return AlertEvent(pipeline=pipeline, rule=rule, result=result)


@pytest.fixture
def filt() -> DeduplicationFilter:
    return DeduplicationFilter(cooldown_minutes=30)


class TestDedupeRecord:
    def test_str_contains_pipeline_and_check(self):
        now = datetime.utcnow()
        r = DedupeRecord(pipeline="p", check_name="c", first_seen=now, last_seen=now)
        assert "p/c" in str(r)

    def test_str_contains_count(self):
        now = datetime.utcnow()
        r = DedupeRecord(pipeline="p", check_name="c", first_seen=now, last_seen=now, count=5)
        assert "x5" in str(r)


class TestIsDuplicate:
    def test_first_event_not_duplicate(self, filt):
        event = _make_event()
        assert filt.is_duplicate(event) is False

    def test_within_cooldown_is_duplicate(self, filt):
        event = _make_event()
        t0 = datetime(2024, 1, 1, 12, 0, 0)
        filt.register(event, now=t0)
        t1 = t0 + timedelta(minutes=10)
        assert filt.is_duplicate(event, now=t1) is True

    def test_after_cooldown_not_duplicate(self, filt):
        event = _make_event()
        t0 = datetime(2024, 1, 1, 12, 0, 0)
        filt.register(event, now=t0)
        t1 = t0 + timedelta(minutes=31)
        assert filt.is_duplicate(event, now=t1) is False

    def test_different_pipelines_independent(self, filt):
        e1 = _make_event(pipeline="pipe_a")
        e2 = _make_event(pipeline="pipe_b")
        t0 = datetime(2024, 1, 1, 12, 0, 0)
        filt.register(e1, now=t0)
        assert filt.is_duplicate(e2, now=t0) is False


class TestRegister:
    def test_register_creates_record(self, filt):
        event = _make_event()
        record = filt.register(event)
        assert isinstance(record, DedupeRecord)
        assert record.count == 1

    def test_register_twice_increments_count(self, filt):
        event = _make_event()
        t0 = datetime(2024, 1, 1, 12, 0, 0)
        filt.register(event, now=t0)
        record = filt.register(event, now=t0 + timedelta(minutes=5))
        assert record.count == 2

    def test_register_updates_last_seen(self, filt):
        event = _make_event()
        t0 = datetime(2024, 1, 1, 12, 0, 0)
        t1 = t0 + timedelta(minutes=5)
        filt.register(event, now=t0)
        record = filt.register(event, now=t1)
        assert record.last_seen == t1


class TestClear:
    def test_clear_all(self, filt):
        filt.register(_make_event("a"))
        filt.register(_make_event("b"))
        removed = filt.clear()
        assert removed == 2

    def test_clear_by_pipeline(self, filt):
        filt.register(_make_event("a"))
        filt.register(_make_event("b"))
        removed = filt.clear(pipeline="a")
        assert removed == 1
        assert filt.is_duplicate(_make_event("b")) is False  # still registered
