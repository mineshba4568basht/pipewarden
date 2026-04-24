"""Tests for pipewarden.scoring."""
from __future__ import annotations

import pytest

from pipewarden.scoring import ScoringPolicy, ScoreResult, score_pipeline
from pipewarden.runner import AlertEvent
from pipewarden.config import AlertRule


def _make_rule(name: str = "check_rows", severity: str = "warning") -> AlertRule:
    return AlertRule(name=name, check="row_count", threshold=0, severity=severity)


def _make_event(severity: str = "warning") -> AlertEvent:
    rule = _make_rule(severity=severity)
    return AlertEvent(pipeline="pipe_a", rule=rule, value=0.0)


# ---------------------------------------------------------------------------
# ScoringPolicy
# ---------------------------------------------------------------------------

class TestScoringPolicy:
    def test_defaults(self):
        p = ScoringPolicy()
        assert p.critical_weight == 40
        assert p.warning_weight == 15
        assert p.info_weight == 5
        assert p.max_score == 100

    def test_invalid_critical_weight_raises(self):
        with pytest.raises(ValueError):
            ScoringPolicy(critical_weight=-1)

    def test_invalid_max_score_zero_raises(self):
        with pytest.raises(ValueError):
            ScoringPolicy(max_score=0)

    def test_invalid_max_score_negative_raises(self):
        with pytest.raises(ValueError):
            ScoringPolicy(max_score=-10)


# ---------------------------------------------------------------------------
# ScoreResult
# ---------------------------------------------------------------------------

class TestScoreResult:
    def _result(self, score=80, max_score=100, event_count=2):
        return ScoreResult(
            pipeline="pipe_a",
            score=score,
            max_score=max_score,
            event_count=event_count,
        )

    def test_healthy_above_half(self):
        assert self._result(score=60).healthy is True

    def test_unhealthy_at_or_below_half(self):
        assert self._result(score=50).healthy is False
        assert self._result(score=0).healthy is False

    def test_pct_calculation(self):
        r = self._result(score=75, max_score=100)
        assert r.pct == 75.0

    def test_pct_zero_when_max_zero(self):
        r = ScoreResult(pipeline="p", score=0, max_score=0, event_count=0)
        assert r.pct == 0.0

    def test_str_contains_pipeline(self):
        assert "pipe_a" in str(self._result())

    def test_str_contains_score(self):
        assert "80/100" in str(self._result(score=80))

    def test_str_healthy_label(self):
        assert "HEALTHY" in str(self._result(score=80))

    def test_str_unhealthy_label(self):
        assert "UNHEALTHY" in str(self._result(score=30))


# ---------------------------------------------------------------------------
# score_pipeline
# ---------------------------------------------------------------------------

class TestScorePipeline:
    def test_no_events_full_score(self):
        r = score_pipeline("pipe_a", [])
        assert r.score == 100
        assert r.event_count == 0

    def test_single_warning_deducts_correctly(self):
        ev = _make_event(severity="warning")
        r = score_pipeline("pipe_a", [ev])
        assert r.score == 100 - 15

    def test_single_critical_deducts_correctly(self):
        ev = _make_event(severity="critical")
        r = score_pipeline("pipe_a", [ev])
        assert r.score == 100 - 40

    def test_score_floored_at_zero(self):
        events = [_make_event(severity="critical")] * 10
        r = score_pipeline("pipe_a", events)
        assert r.score == 0

    def test_deductions_list_populated(self):
        ev = _make_event(severity="warning")
        r = score_pipeline("pipe_a", [ev])
        assert len(r.deductions) == 1
        assert "-15" in r.deductions[0]

    def test_custom_policy_respected(self):
        policy = ScoringPolicy(warning_weight=10, max_score=50)
        ev = _make_event(severity="warning")
        r = score_pipeline("pipe_a", [ev], policy)
        assert r.score == 40
        assert r.max_score == 50

    def test_unknown_severity_no_deduction(self):
        rule = _make_rule(severity="debug")
        ev = AlertEvent(pipeline="pipe_a", rule=rule, value=0.0)
        r = score_pipeline("pipe_a", [ev])
        assert r.score == 100
