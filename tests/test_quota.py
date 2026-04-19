"""Tests for pipewarden.quota."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewarden.quota import QuotaManager, QuotaPolicy, QuotaResult
from pipewarden.runner import AlertEvent
from pipewarden.config import AlertRule


def _make_event(pipeline: str = "pipe_a") -> AlertEvent:
    rule = AlertRule(name="row_count", check="row_count", threshold=100)
    return AlertEvent(pipeline=pipeline, rule=rule, observed=50.0)


class TestQuotaPolicy:
    def test_defaults(self):
        p = QuotaPolicy()
        assert p.max_alerts == 10
        assert p.window_minutes == 60

    def test_invalid_max_alerts_raises(self):
        with pytest.raises(ValueError):
            QuotaPolicy(max_alerts=0)

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError):
            QuotaPolicy(window_minutes=0)

    def test_str(self):
        p = QuotaPolicy(max_alerts=5, window_minutes=30)
        assert "5" in str(p)
        assert "30" in str(p)


class TestQuotaResult:
    def test_str_allowed(self):
        event = _make_event()
        r = QuotaResult(event=event, allowed=True, current_count=1, limit=10)
        assert "allowed" in str(r)

    def test_str_blocked(self):
        event = _make_event()
        r = QuotaResult(event=event, allowed=False, current_count=10, limit=10)
        assert "blocked" in str(r)


class TestQuotaManager:
    def test_first_alert_allowed(self):
        mgr = QuotaManager(policy=QuotaPolicy(max_alerts=3))
        result = mgr.check(_make_event())
        assert result.allowed is True
        assert result.current_count == 1

    def test_exceeding_quota_blocked(self):
        mgr = QuotaManager(policy=QuotaPolicy(max_alerts=2))
        event = _make_event()
        mgr.check(event)
        mgr.check(event)
        result = mgr.check(event)
        assert result.allowed is False
        assert result.current_count == 2

    def test_old_entries_expire(self):
        mgr = QuotaManager(policy=QuotaPolicy(max_alerts=2, window_minutes=10))
        event = _make_event()
        old = datetime.utcnow() - timedelta(minutes=20)
        mgr._log["pipe_a"] = [old, old]
        result = mgr.check(event)
        assert result.allowed is True

    def test_reset_clears_pipeline(self):
        mgr = QuotaManager(policy=QuotaPolicy(max_alerts=2))
        event = _make_event()
        mgr.check(event)
        mgr.reset("pipe_a")
        assert mgr.usage("pipe_a") == 0

    def test_usage_counts_within_window(self):
        mgr = QuotaManager(policy=QuotaPolicy(max_alerts=5, window_minutes=60))
        event = _make_event()
        mgr.check(event)
        mgr.check(event)
        assert mgr.usage("pipe_a") == 2

    def test_different_pipelines_tracked_separately(self):
        mgr = QuotaManager(policy=QuotaPolicy(max_alerts=1))
        mgr.check(_make_event("pipe_a"))
        result = mgr.check(_make_event("pipe_b"))
        assert result.allowed is True
