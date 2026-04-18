"""Tests for pipewarden.backoff."""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from pipewarden.backoff import BackoffPolicy, BackoffState, BackoffManager


class TestBackoffPolicy:
    def test_defaults(self):
        p = BackoffPolicy()
        assert p.base_delay == 60.0
        assert p.multiplier == 2.0
        assert p.max_delay == 3600.0
        assert p.max_attempts == 5

    def test_invalid_base_delay_raises(self):
        with pytest.raises(ValueError):
            BackoffPolicy(base_delay=0)

    def test_invalid_multiplier_raises(self):
        with pytest.raises(ValueError):
            BackoffPolicy(multiplier=0.5)

    def test_invalid_max_attempts_raises(self):
        with pytest.raises(ValueError):
            BackoffPolicy(max_attempts=0)

    def test_delay_for_first_attempt(self):
        p = BackoffPolicy(base_delay=10.0, multiplier=2.0)
        assert p.delay_for(1) == 10.0

    def test_delay_doubles_each_attempt(self):
        p = BackoffPolicy(base_delay=10.0, multiplier=2.0)
        assert p.delay_for(2) == 20.0
        assert p.delay_for(3) == 40.0

    def test_delay_capped_at_max(self):
        p = BackoffPolicy(base_delay=100.0, multiplier=10.0, max_delay=500.0)
        assert p.delay_for(5) == 500.0

    def test_next_retry_at_returns_none_when_exhausted(self):
        p = BackoffPolicy(max_attempts=3)
        now = datetime.utcnow()
        assert p.next_retry_at(now, 3) is None

    def test_next_retry_at_returns_future(self):
        p = BackoffPolicy(base_delay=60.0, multiplier=1.0, max_attempts=5)
        now = datetime.utcnow()
        result = p.next_retry_at(now, 1)
        assert result is not None
        assert result > now

    def test_str_contains_base_delay(self):
        p = BackoffPolicy(base_delay=30.0)
        assert "30.0" in str(p)


class TestBackoffState:
    def test_is_due_with_no_attempts(self):
        s = BackoffState("pipe", "check")
        assert s.is_due() is True

    def test_record_increments_attempts(self):
        s = BackoffState("pipe", "check")
        s.record_attempt()
        assert s.attempts == 1
        assert s.last_attempt is not None

    def test_not_due_immediately_after_attempt(self):
        policy = BackoffPolicy(base_delay=3600.0)
        s = BackoffState("pipe", "check", _policy=policy)
        s.record_attempt()
        assert s.is_due() is False

    def test_due_after_delay_passed(self):
        policy = BackoffPolicy(base_delay=10.0, multiplier=1.0)
        s = BackoffState("pipe", "check", _policy=policy)
        s.attempts = 1
        s.last_attempt = datetime.utcnow() - timedelta(seconds=20)
        assert s.is_due() is True

    def test_reset_clears_state(self):
        s = BackoffState("pipe", "check")
        s.record_attempt()
        s.reset()
        assert s.attempts == 0
        assert s.last_attempt is None


class TestBackoffManager:
    def test_should_alert_initially_true(self):
        mgr = BackoffManager()
        assert mgr.should_alert("pipe", "check") is True

    def test_should_alert_false_after_record(self):
        policy = BackoffPolicy(base_delay=3600.0)
        mgr = BackoffManager(policy)
        mgr.record("pipe", "check")
        assert mgr.should_alert("pipe", "check") is False

    def test_reset_allows_immediate_alert(self):
        policy = BackoffPolicy(base_delay=3600.0)
        mgr = BackoffManager(policy)
        mgr.record("pipe", "check")
        mgr.reset("pipe", "check")
        assert mgr.should_alert("pipe", "check") is True

    def test_independent_states_per_pipeline(self):
        mgr = BackoffManager(BackoffPolicy(base_delay=3600.0))
        mgr.record("pipe_a", "check")
        assert mgr.should_alert("pipe_b", "check") is True
