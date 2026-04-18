"""Tests for pipewarden.circuit_breaker."""
from __future__ import annotations
import time
import pytest
from pipewarden.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitState,
)


class TestCircuitBreakerConstruction:
    def test_defaults(self):
        cb = CircuitBreaker(pipeline="p1")
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError, match="failure_threshold"):
            CircuitBreaker(pipeline="p", failure_threshold=0)

    def test_invalid_recovery_timeout_raises(self):
        with pytest.raises(ValueError, match="recovery_timeout"):
            CircuitBreaker(pipeline="p", recovery_timeout=0)


class TestCircuitBreakerState:
    def test_initial_state_closed(self):
        cb = CircuitBreaker(pipeline="p")
        assert cb.state == CircuitState.CLOSED

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(pipeline="p", failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_does_not_open_before_threshold(self):
        cb = CircuitBreaker(pipeline="p", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

    def test_allow_request_closed(self):
        cb = CircuitBreaker(pipeline="p")
        assert cb.allow_request() is True

    def test_deny_request_when_open(self):
        cb = CircuitBreaker(pipeline="p", failure_threshold=1)
        cb.record_failure()
        assert cb.allow_request() is False

    def test_reset_closes_circuit(self):
        cb = CircuitBreaker(pipeline="p", failure_threshold=1)
        cb.record_failure()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_half_open_after_recovery_timeout(self):
        cb = CircuitBreaker(pipeline="p", failure_threshold=1, recovery_timeout=1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(1.05)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.allow_request() is True

    def test_str_representation(self):
        cb = CircuitBreaker(pipeline="pipe")
        s = str(cb)
        assert "pipe" in s
        assert "closed" in s


class TestCircuitBreakerRegistry:
    def test_get_creates_new(self):
        reg = CircuitBreakerRegistry()
        cb = reg.get("p1")
        assert cb.pipeline == "p1"

    def test_get_returns_same_instance(self):
        reg = CircuitBreakerRegistry()
        cb1 = reg.get("p1")
        cb2 = reg.get("p1")
        assert cb1 is cb2

    def test_all_returns_all_breakers(self):
        reg = CircuitBreakerRegistry()
        reg.get("a")
        reg.get("b")
        assert len(reg.all()) == 2

    def test_reset_existing(self):
        reg = CircuitBreakerRegistry()
        cb = reg.get("p", failure_threshold=1)
        cb.record_failure()
        result = reg.reset("p")
        assert result is True
        assert cb.state == CircuitState.CLOSED

    def test_reset_nonexistent_returns_false(self):
        reg = CircuitBreakerRegistry()
        assert reg.reset("ghost") is False
