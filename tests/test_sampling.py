"""Tests for pipewarden.sampling."""
from __future__ import annotations

import pytest

from pipewarden.sampling import (
    SamplingPolicy,
    SampleResult,
    batch_sample,
    kept_events,
    sample_event,
)
from pipewarden.runner import AlertEvent
from pipewarden.config import AlertRule
from pipewarden.checks import CheckResult, CheckStatus


def _make_rule(name: str = "r", severity: str = "warning") -> AlertRule:
    return AlertRule(name=name, check="row_count", pipeline="pipe", threshold=10, severity=severity)


def _make_event(pipeline: str = "pipe") -> AlertEvent:
    rule = _make_rule()
    result = CheckResult(check="row_count", status=CheckStatus.FAIL, value=5, threshold=10)
    return AlertEvent(rule=rule, result=result, pipeline=pipeline)


class TestSamplingPolicy:
    def test_default_rate_is_one(self):
        p = SamplingPolicy()
        assert p.rate == 1.0

    def test_invalid_rate_zero_raises(self):
        with pytest.raises(ValueError):
            SamplingPolicy(rate=0.0)

    def test_invalid_rate_above_one_raises(self):
        with pytest.raises(ValueError):
            SamplingPolicy(rate=1.5)

    def test_str_contains_rate(self):
        p = SamplingPolicy(rate=0.5)
        assert "50%" in str(p)


class TestSampleEvent:
    def test_rate_one_always_keeps(self):
        policy = SamplingPolicy(rate=1.0)
        event = _make_event()
        for _ in range(20):
            result = sample_event(event, policy)
            assert result.kept is True

    def test_seeded_policy_is_deterministic(self):
        event = _make_event()
        r1 = [sample_event(event, SamplingPolicy(rate=0.5, seed=42)).kept for _ in range(10)]
        r2 = [sample_event(event, SamplingPolicy(rate=0.5, seed=42)).kept for _ in range(10)]
        assert r1 == r2

    def test_sample_result_str_kept(self):
        policy = SamplingPolicy(rate=1.0)
        result = sample_event(_make_event(), policy)
        assert "KEPT" in str(result)

    def test_sample_result_str_dropped(self):
        policy = SamplingPolicy(rate=1.0, seed=0)
        result = SampleResult(event=_make_event(), kept=False, rate=1.0)
        assert "DROPPED" in str(result)


class TestBatchSample:
    def test_batch_returns_same_length(self):
        events = [_make_event() for _ in range(5)]
        results = batch_sample(events, SamplingPolicy(rate=1.0))
        assert len(results) == 5

    def test_kept_events_filters_correctly(self):
        events = [_make_event() for _ in range(4)]
        policy = SamplingPolicy(rate=1.0)
        results = batch_sample(events, policy)
        assert len(kept_events(results)) == 4

    def test_kept_events_empty_when_all_dropped(self):
        events = [_make_event()]
        results = [SampleResult(event=e, kept=False, rate=0.1) for e in events]
        assert kept_events(results) == []
