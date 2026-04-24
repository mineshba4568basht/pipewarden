"""Tests for pipewarden.aggregation."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewarden.aggregation import (
    AggregatedBucket,
    AggregationPolicy,
    aggregate,
    _group_key,
)
from pipewarden.config import AlertRule
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.runner import AlertEvent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rule(name: str = "row_count", severity: str = "warning") -> AlertRule:
    return AlertRule(name=name, check="row_count", threshold=100, severity=severity)


def _make_event(
    pipeline: str = "pipe_a",
    check: str = "row_count",
    severity: str = "warning",
    offset_seconds: int = 0,
) -> AlertEvent:
    rule = _make_rule(name=check, severity=severity)
    result = CheckResult(rule=rule, status=CheckStatus.FAIL, value=0.0)
    event = AlertEvent(pipeline=pipeline, check_result=result, rule=rule)
    event.triggered_at = datetime.utcnow() - timedelta(seconds=offset_seconds)
    return event


# ---------------------------------------------------------------------------
# AggregationPolicy construction
# ---------------------------------------------------------------------------

class TestAggregationPolicy:
    def test_defaults(self):
        p = AggregationPolicy()
        assert p.window_seconds == 60
        assert p.max_events == 100
        assert p.group_by == "pipeline"

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            AggregationPolicy(window_seconds=0)

    def test_invalid_max_events_raises(self):
        with pytest.raises(ValueError, match="max_events"):
            AggregationPolicy(max_events=-1)

    def test_invalid_group_by_raises(self):
        with pytest.raises(ValueError, match="group_by"):
            AggregationPolicy(group_by="unknown")

    def test_valid_group_by_check(self):
        p = AggregationPolicy(group_by="check")
        assert p.group_by == "check"

    def test_valid_group_by_severity(self):
        p = AggregationPolicy(group_by="severity")
        assert p.group_by == "severity"


# ---------------------------------------------------------------------------
# AggregatedBucket
# ---------------------------------------------------------------------------

class TestAggregatedBucket:
    def test_count_empty(self):
        b = AggregatedBucket(key="pipe_a")
        assert b.count == 0

    def test_count_with_events(self):
        b = AggregatedBucket(key="pipe_a", events=[_make_event(), _make_event()])
        assert b.count == 2

    def test_severities(self):
        b = AggregatedBucket(
            key="pipe_a",
            events=[_make_event(severity="warning"), _make_event(severity="critical")],
        )
        assert set(b.severities) == {"warning", "critical"}

    def test_str(self):
        b = AggregatedBucket(key="pipe_a")
        assert "pipe_a" in str(b)
        assert "count=0" in str(b)


# ---------------------------------------------------------------------------
# aggregate()
# ---------------------------------------------------------------------------

class TestAggregate:
    def test_empty_events_returns_empty(self):
        result = aggregate([], AggregationPolicy())
        assert result == []

    def test_events_within_window_are_included(self):
        events = [_make_event(offset_seconds=10)]
        buckets = aggregate(events, AggregationPolicy(window_seconds=60))
        assert len(buckets) == 1
        assert buckets[0].count == 1

    def test_events_outside_window_are_excluded(self):
        events = [_make_event(offset_seconds=120)]
        buckets = aggregate(events, AggregationPolicy(window_seconds=60))
        assert buckets == []

    def test_group_by_pipeline(self):
        events = [
            _make_event(pipeline="pipe_a"),
            _make_event(pipeline="pipe_b"),
            _make_event(pipeline="pipe_a"),
        ]
        buckets = aggregate(events, AggregationPolicy(group_by="pipeline"))
        keys = {b.key for b in buckets}
        assert keys == {"pipe_a", "pipe_b"}
        counts = {b.key: b.count for b in buckets}
        assert counts["pipe_a"] == 2

    def test_group_by_severity(self):
        events = [
            _make_event(severity="warning"),
            _make_event(severity="critical"),
            _make_event(severity="warning"),
        ]
        buckets = aggregate(events, AggregationPolicy(group_by="severity"))
        keys = {b.key for b in buckets}
        assert keys == {"warning", "critical"}

    def test_max_events_limits_bucket_size(self):
        events = [_make_event() for _ in range(10)]
        buckets = aggregate(events, AggregationPolicy(max_events=3))
        total = sum(b.count for b in buckets)
        assert total <= 3

    def test_now_override_shifts_cutoff(self):
        future = datetime.utcnow() + timedelta(hours=1)
        events = [_make_event(offset_seconds=0)]
        # All events are in the past relative to 'future', still within 60 s window
        buckets = aggregate(events, AggregationPolicy(window_seconds=60), now=future)
        # Events are 3600 s before 'future', outside 60 s window
        assert buckets == []
