"""Tests for pipewarden.ratelimit."""
from __future__ import annotations
from datetime import datetime, timedelta
import pytest

from pipewarden.ratelimit import RateLimitPolicy, RateLimiter, RateLimitResult
from pipewarden.runner import AlertEvent
from pipewarden.config import AlertRule


def _make_event(pipeline: str = "pipe_a") -> AlertEvent:
    rule = AlertRule(name="row_count", check="row_count", threshold=100)
    return AlertEvent(pipeline=pipeline, rule=rule, value=50.0, message="Low rows")


class TestRateLimitPolicy:
    def test_defaults(self):
        p = RateLimitPolicy()
        assert p.max_alerts == 5
        assert p.window_seconds == 300

    def test_invalid_max_alerts_raises(self):
        with pytest.raises(ValueError):
            RateLimitPolicy(max_alerts=0)

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError):
            RateLimitPolicy(window_seconds=0)

    def test_str(self):
        p = RateLimitPolicy(max_alerts=3, window_seconds=60)
        assert "3" in str(p)
        assert "60" in str(p)


class TestRateLimiter:
    def test_first_alert_allowed(self):
        limiter = RateLimiter(RateLimitPolicy(max_alerts=3, window_seconds=60))
        result = limiter.check(_make_event())
        assert result.allowed is True
        assert result.current_count == 1

    def test_alerts_within_limit_all_allowed(self):
        limiter = RateLimiter(RateLimitPolicy(max_alerts=3, window_seconds=60))
        event = _make_event()
        now = datetime.utcnow()
        for i in range(3):
            r = limiter.check(event, now=now + timedelta(seconds=i))
            assert r.allowed is True

    def test_exceeding_limit_blocked(self):
        limiter = RateLimiter(RateLimitPolicy(max_alerts=2, window_seconds=60))
        event = _make_event()
        now = datetime.utcnow()
        limiter.check(event, now=now)
        limiter.check(event, now=now + timedelta(seconds=1))
        result = limiter.check(event, now=now + timedelta(seconds=2))
        assert result.allowed is False

    def test_old_events_expire(self):
        limiter = RateLimiter(RateLimitPolicy(max_alerts=2, window_seconds=30))
        event = _make_event()
        past = datetime.utcnow() - timedelta(seconds=60)
        limiter.check(event, now=past)
        limiter.check(event, now=past + timedelta(seconds=1))
        now = datetime.utcnow()
        result = limiter.check(event, now=now)
        assert result.allowed is True

    def test_different_pipelines_independent(self):
        limiter = RateLimiter(RateLimitPolicy(max_alerts=1, window_seconds=60))
        now = datetime.utcnow()
        limiter.check(_make_event("pipe_a"), now=now)
        result = limiter.check(_make_event("pipe_b"), now=now)
        assert result.allowed is True

    def test_reset_clears_pipeline(self):
        limiter = RateLimiter(RateLimitPolicy(max_alerts=1, window_seconds=60))
        event = _make_event()
        now = datetime.utcnow()
        limiter.check(event, now=now)
        limiter.reset("pipe_a")
        result = limiter.check(event, now=now)
        assert result.allowed is True

    def test_reset_all_clears_everything(self):
        limiter = RateLimiter(RateLimitPolicy(max_alerts=1, window_seconds=60))
        now = datetime.utcnow()
        limiter.check(_make_event("pipe_a"), now=now)
        limiter.check(_make_event("pipe_b"), now=now)
        limiter.reset_all()
        assert limiter.check(_make_event("pipe_a"), now=now).allowed is True


class TestRateLimitResult:
    def test_str_allowed(self):
        event = _make_event()
        r = RateLimitResult(event=event, allowed=True, current_count=1, limit=5)
        assert "ALLOWED" in str(r)

    def test_str_blocked(self):
        event = _make_event()
        r = RateLimitResult(event=event, allowed=False, current_count=5, limit=5)
        assert "BLOCKED" in str(r)
