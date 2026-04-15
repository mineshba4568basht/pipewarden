"""Tests for pipewarden.tags — tag-based filtering and grouping."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewarden.tags import TagFilter, group_by_tag, filter_report_by_tags


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(*tags: str) -> MagicMock:
    """Create a mock AlertEvent whose rule carries *tags*."""
    event = MagicMock()
    event.rule.tags = list(tags)
    return event


# ---------------------------------------------------------------------------
# TagFilter.matches
# ---------------------------------------------------------------------------

class TestTagFilterMatches:
    def test_empty_filter_accepts_all(self):
        tf = TagFilter()
        assert tf.matches(_make_event("critical")) is True
        assert tf.matches(_make_event()) is True

    def test_include_tag_matches_event_with_that_tag(self):
        tf = TagFilter(include_tags=frozenset(["finance"]))
        assert tf.matches(_make_event("finance", "daily")) is True

    def test_include_tag_rejects_event_without_tag(self):
        tf = TagFilter(include_tags=frozenset(["finance"]))
        assert tf.matches(_make_event("ops")) is False

    def test_exclude_tag_drops_event(self):
        tf = TagFilter(exclude_tags=frozenset(["flaky"]))
        assert tf.matches(_make_event("finance", "flaky")) is False

    def test_exclude_takes_precedence_over_include(self):
        tf = TagFilter(
            include_tags=frozenset(["finance"]),
            exclude_tags=frozenset(["flaky"]),
        )
        assert tf.matches(_make_event("finance", "flaky")) is False

    def test_event_with_no_tags_rejected_when_include_set(self):
        tf = TagFilter(include_tags=frozenset(["finance"]))
        assert tf.matches(_make_event()) is False

    def test_list_inputs_normalised_to_frozenset(self):
        tf = TagFilter(include_tags=["a"], exclude_tags=["b"])  # type: ignore[arg-type]
        assert isinstance(tf.include_tags, frozenset)
        assert isinstance(tf.exclude_tags, frozenset)


# ---------------------------------------------------------------------------
# TagFilter.apply
# ---------------------------------------------------------------------------

class TestTagFilterApply:
    def test_apply_returns_matching_subset(self):
        tf = TagFilter(include_tags=frozenset(["ops"]))
        events = [_make_event("ops"), _make_event("finance"), _make_event("ops", "finance")]
        result = tf.apply(events)
        assert len(result) == 2

    def test_apply_empty_list(self):
        tf = TagFilter(include_tags=frozenset(["ops"]))
        assert tf.apply([]) == []


# ---------------------------------------------------------------------------
# group_by_tag
# ---------------------------------------------------------------------------

class TestGroupByTag:
    def test_single_tag_event_placed_in_correct_bucket(self):
        events = [_make_event("ops")]
        groups = group_by_tag(events)
        assert "ops" in groups
        assert events[0] in groups["ops"]

    def test_multi_tag_event_appears_in_multiple_buckets(self):
        event = _make_event("ops", "finance")
        groups = group_by_tag([event])
        assert event in groups["ops"]
        assert event in groups["finance"]

    def test_untagged_event_goes_to_untagged_bucket(self):
        event = _make_event()
        groups = group_by_tag([event])
        assert "(untagged)" in groups
        assert event in groups["(untagged)"]


# ---------------------------------------------------------------------------
# filter_report_by_tags convenience wrapper
# ---------------------------------------------------------------------------

class TestFilterReportByTags:
    def test_delegates_to_tag_filter(self):
        report = MagicMock()
        report.alert_events = [_make_event("finance"), _make_event("ops")]
        result = filter_report_by_tags(report, include_tags=["finance"])
        assert len(result) == 1
        assert result[0].rule.tags == ["finance"]

    def test_empty_include_returns_all_events(self):
        report = MagicMock()
        report.alert_events = [_make_event("a"), _make_event("b")]
        result = filter_report_by_tags(report)
        assert len(result) == 2
