"""Tests for pipewarden.shedding."""
from __future__ import annotations

import pytest

from pipewarden.shedding import (
    SheddingPolicy,
    ShedResult,
    apply_shedding,
)
from pipewarden.runner import AlertEvent
from pipewarden.config import AlertRule


def _make_rule(severity: str = "warning") -> AlertRule:
    return AlertRule(name="test_rule", check="row_count", threshold=10, severity=severity)


def _make_event(severity: str = "warning") -> AlertEvent:
    return AlertEvent(rule=_make_rule(severity), value=5.0)


# ---------------------------------------------------------------------------
# SheddingPolicy construction
# ---------------------------------------------------------------------------

class TestSheddingPolicy:
    def test_defaults(self):
        p = SheddingPolicy()
        assert p.max_queue_depth == 100
        assert p.min_priority == 0
        assert p.shed_on_overload is True

    def test_invalid_max_queue_depth_raises(self):
        with pytest.raises(ValueError):
            SheddingPolicy(max_queue_depth=0)

    def test_invalid_min_priority_raises(self):
        with pytest.raises(ValueError):
            SheddingPolicy(min_priority=11)

    def test_str_contains_key_fields(self):
        p = SheddingPolicy(max_queue_depth=50, min_priority=5)
        s = str(p)
        assert "50" in s
        assert "5" in s


# ---------------------------------------------------------------------------
# ShedResult
# ---------------------------------------------------------------------------

class TestShedResult:
    def test_total_counts_all(self):
        e1 = _make_event()
        e2 = _make_event()
        r = ShedResult(accepted=[e1], shed=[e2])
        assert r.total == 2

    def test_shed_count(self):
        r = ShedResult(shed=[_make_event(), _make_event()])
        assert r.shed_count == 2

    def test_str_contains_counts(self):
        r = ShedResult(accepted=[_make_event()], shed=[_make_event()])
        s = str(r)
        assert "total=2" in s
        assert "accepted=1" in s
        assert "shed=1" in s


# ---------------------------------------------------------------------------
# apply_shedding
# ---------------------------------------------------------------------------

class TestApplyShedding:
    def test_no_overload_accepts_all(self):
        policy = SheddingPolicy(max_queue_depth=100, min_priority=5)
        events = [_make_event("info"), _make_event("warning"), _make_event("critical")]
        result = apply_shedding(events, policy, current_queue_depth=10)
        assert len(result.accepted) == 3
        assert len(result.shed) == 0

    def test_overload_sheds_low_priority(self):
        policy = SheddingPolicy(max_queue_depth=5, min_priority=5)
        events = [_make_event("info"), _make_event("critical")]
        result = apply_shedding(events, policy, current_queue_depth=5)
        assert len(result.shed) == 1
        assert result.shed[0].rule.severity == "info"
        assert len(result.accepted) == 1
        assert result.accepted[0].rule.severity == "critical"

    def test_shed_on_overload_false_accepts_all(self):
        policy = SheddingPolicy(max_queue_depth=5, min_priority=5, shed_on_overload=False)
        events = [_make_event("info"), _make_event("info")]
        result = apply_shedding(events, policy, current_queue_depth=100)
        assert len(result.accepted) == 2

    def test_empty_events_returns_empty_result(self):
        policy = SheddingPolicy()
        result = apply_shedding([], policy, current_queue_depth=200)
        assert result.total == 0
