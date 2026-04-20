"""Tests for pipewarden.partitioning."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from pipewarden.partitioning import (
    Partition,
    PartitionResult,
    partition_by,
    partition_by_pipeline,
    partition_by_severity,
)


def _make_event(pipeline: str, severity: str = "warning") -> MagicMock:
    event = MagicMock()
    event.rule.pipeline = pipeline
    event.rule.severity = severity
    return event


class TestPartition:
    def test_count_empty(self):
        p = Partition(name="a")
        assert p.count == 0

    def test_count_with_events(self):
        p = Partition(name="a", events=[MagicMock(), MagicMock()])
        assert p.count == 2


class TestPartitionResult:
    def test_partition_names_sorted(self):
        r = PartitionResult(
            partitions={"z": Partition("z"), "a": Partition("a")}
        )
        assert r.partition_names == ["a", "z"]

    def test_total_events(self):
        r = PartitionResult(
            partitions={
                "a": Partition("a", events=[MagicMock()]),
                "b": Partition("b", events=[MagicMock(), MagicMock()]),
            }
        )
        assert r.total_events == 3

    def test_get_existing(self):
        part = Partition("x")
        r = PartitionResult(partitions={"x": part})
        assert r.get("x") is part

    def test_get_missing_returns_none(self):
        r = PartitionResult()
        assert r.get("missing") is None


class TestPartitionBy:
    def test_empty_events(self):
        result = partition_by([], key_fn=lambda e: e.rule.pipeline)
        assert result.total_events == 0
        assert result.partition_names == []

    def test_single_event(self):
        events = [_make_event("pipe_a")]
        result = partition_by(events, key_fn=lambda e: e.rule.pipeline)
        assert "pipe_a" in result.partitions
        assert result.partitions["pipe_a"].count == 1

    def test_multiple_events_same_key(self):
        events = [_make_event("pipe_a"), _make_event("pipe_a")]
        result = partition_by_pipeline(events)
        assert result.partitions["pipe_a"].count == 2

    def test_multiple_events_different_keys(self):
        events = [_make_event("pipe_a"), _make_event("pipe_b"), _make_event("pipe_a")]
        result = partition_by_pipeline(events)
        assert result.partitions["pipe_a"].count == 2
        assert result.partitions["pipe_b"].count == 1
        assert result.total_events == 3

    def test_partition_by_severity(self):
        events = [
            _make_event("p", severity="critical"),
            _make_event("p", severity="warning"),
            _make_event("p", severity="critical"),
        ]
        result = partition_by_severity(events)
        assert result.partitions["critical"].count == 2
        assert result.partitions["warning"].count == 1

    def test_custom_key_fn(self):
        events = [_make_event("pipe_a", "critical"), _make_event("pipe_b", "warning")]
        result = partition_by(events, key_fn=lambda e: e.rule.severity)
        assert "critical" in result.partitions
        assert "warning" in result.partitions
