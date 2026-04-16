"""Tests for pipewarden.throttle."""
from __future__ import annotations
from datetime import datetime, timedelta
import pytest
from pipewarden.throttle import ThrottleManager, ThrottlePolicy, ThrottleRecord


T0 = datetime(2024, 1, 1, 12, 0, 0)


class TestThrottlePolicy:
    def test_default_cooldown(self):
        p = ThrottlePolicy()
        assert p.cooldown_minutes == 30

    def test_invalid_cooldown_raises(self):
        with pytest.raises(ValueError):
            ThrottlePolicy(cooldown_minutes=0)


class TestThrottleRecord:
    def test_str_contains_pipeline_and_check(self):
        rec = ThrottleRecord(pipeline="p", check="c", first_fired=T0, last_fired=T0)
        s = str(rec)
        assert "p" in s and "c" in s

    def test_str_contains_suppressed_count(self):
        rec = ThrottleRecord(pipeline="p", check="c", first_fired=T0, last_fired=T0, suppressed_count=3)
        assert "3" in str(rec)


class TestThrottleManager:
    def _manager(self, cooldown=10):
        return ThrottleManager(policy=ThrottlePolicy(cooldown_minutes=cooldown))

    def test_not_throttled_before_first_record(self):
        m = self._manager()
        assert not m.is_throttled("pipe", "check", now=T0)

    def test_throttled_immediately_after_record(self):
        m = self._manager(cooldown=10)
        m.record("pipe", "check", now=T0)
        assert m.is_throttled("pipe", "check", now=T0 + timedelta(minutes=1))

    def test_not_throttled_after_cooldown_expires(self):
        m = self._manager(cooldown=10)
        m.record("pipe", "check", now=T0)
        assert not m.is_throttled("pipe", "check", now=T0 + timedelta(minutes=11))

    def test_suppressed_count_increments(self):
        m = self._manager(cooldown=30)
        m.record("pipe", "check", now=T0)
        m.record("pipe", "check", now=T0 + timedelta(minutes=5))
        rec = m.record("pipe", "check", now=T0 + timedelta(minutes=10))
        assert rec.suppressed_count == 2

    def test_suppressed_count_resets_after_cooldown(self):
        m = self._manager(cooldown=10)
        m.record("pipe", "check", now=T0)
        rec = m.record("pipe", "check", now=T0 + timedelta(minutes=15))
        assert rec.suppressed_count == 0

    def test_max_suppressed_limits_throttle(self):
        policy = ThrottlePolicy(cooldown_minutes=30, max_suppressed=1)
        m = ThrottleManager(policy=policy)
        m.record("pipe", "check", now=T0)
        m.record("pipe", "check", now=T0 + timedelta(minutes=5))  # suppressed=1
        m.record("pipe", "check", now=T0 + timedelta(minutes=10))  # suppressed=2
        assert not m.is_throttled("pipe", "check", now=T0 + timedelta(minutes=12))

    def test_clear_removes_record(self):
        m = self._manager()
        m.record("pipe", "check", now=T0)
        m.clear("pipe", "check")
        assert not m.is_throttled("pipe", "check", now=T0 + timedelta(minutes=1))

    def test_active_records_returns_all(self):
        m = self._manager()
        m.record("p1", "c1", now=T0)
        m.record("p2", "c2", now=T0)
        assert len(m.active_records()) == 2

    def test_different_pipelines_tracked_independently(self):
        m = self._manager(cooldown=10)
        m.record("p1", "c", now=T0)
        assert not m.is_throttled("p2", "c", now=T0 + timedelta(minutes=1))
