"""Tests for pipewarden.grouping."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewarden.grouping import (
    AlertGroup,
    group_by_check,
    group_by_pipeline,
    group_by_severity,
    group_events,
)


def _make_event(pipeline: str, severity: str, check_name: str):
    rule = MagicMock()
    rule.severity = severity
    result = MagicMock()
    result.check_name = check_name
    event = MagicMock()
    event.pipeline = pipeline
    event.rule = rule
    event.result = result
    return event


@pytest.fixture()
def events():
    return [
        _make_event("pipe_a", "critical", "row_count"),
        _make_event("pipe_a", "warning", "null_check"),
        _make_event("pipe_b", "info", "row_count"),
    ]


class TestAlertGroup:
    def test_count(self, events):
        g = AlertGroup(key="pipe_a", events=events[:2])
        assert g.count == 2

    def test_highest_severity_critical_wins(self, events):
        g = AlertGroup(key="pipe_a", events=events[:2])
        assert g.highest_severity == "critical"

    def test_highest_severity_info_only(self, events):
        g = AlertGroup(key="pipe_b", events=[events[2]])
        assert g.highest_severity == "info"

    def test_str_contains_key_and_count(self, events):
        g = AlertGroup(key="pipe_a", events=events[:2])
        s = str(g)
        assert "pipe_a" in s
        assert "count=2" in s


class TestGroupEvents:
    def test_group_by_pipeline_creates_two_groups(self, events):
        groups = group_events(events, key_fn=group_by_pipeline)
        assert set(groups.keys()) == {"pipe_a", "pipe_b"}

    def test_group_by_pipeline_counts(self, events):
        groups = group_events(events, key_fn=group_by_pipeline)
        assert groups["pipe_a"].count == 2
        assert groups["pipe_b"].count == 1

    def test_group_by_severity(self, events):
        groups = group_events(events, key_fn=group_by_severity)
        assert "critical" in groups
        assert "warning" in groups
        assert "info" in groups

    def test_group_by_check(self, events):
        groups = group_events(events, key_fn=group_by_check)
        assert "row_count" in groups
        assert groups["row_count"].count == 2

    def test_empty_events_returns_empty_dict(self):
        assert group_events([]) == {}

    def test_default_key_fn_is_pipeline(self, events):
        groups = group_events(events)
        assert "pipe_a" in groups
