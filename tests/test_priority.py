"""Tests for pipewarden.priority."""
from __future__ import annotations
import pytest
from types import SimpleNamespace
from pipewarden.priority import PriorityPolicy, PriorityScore, SEVERITY_SCORES


def _make_event(severity: str = "warning", tags: list | None = None, pipeline: str = "pipe_a", check: str = "row_count"):
    rule = SimpleNamespace(severity=severity, name=check, tags=tags or [])
    return SimpleNamespace(pipeline=pipeline, rule=rule)


class TestPriorityScore:
    def test_total_sums_parts(self):
        s = PriorityScore("p", "c", base_score=50, recurrence_bonus=10, tag_bonus=20)
        assert s.total == 80

    def test_str_contains_pipeline_and_check(self):
        s = PriorityScore("pipe", "chk", 50, 0, 0)
        assert "pipe" in str(s)
        assert "chk" in str(s)

    def test_str_contains_total(self):
        s = PriorityScore("p", "c", 50, 5, 20)
        assert "total=75" in str(s)


class TestPriorityPolicy:
    def test_defaults(self):
        policy = PriorityPolicy()
        assert policy.tag_bonus == 20
        assert policy.recurrence_weight == 5
        assert policy.max_recurrence_bonus == 50
        assert policy.high_priority_tags == []

    def test_invalid_tag_bonus_raises(self):
        with pytest.raises(ValueError):
            PriorityPolicy(tag_bonus=-1)

    def test_invalid_recurrence_weight_raises(self):
        with pytest.raises(ValueError):
            PriorityPolicy(recurrence_weight=-1)

    def test_invalid_max_recurrence_bonus_raises(self):
        with pytest.raises(ValueError):
            PriorityPolicy(max_recurrence_bonus=-1)

    def test_score_base_warning(self):
        policy = PriorityPolicy()
        event = _make_event(severity="warning")
        result = policy.score(event)
        assert result.base_score == SEVERITY_SCORES["warning"]

    def test_score_base_critical(self):
        policy = PriorityPolicy()
        event = _make_event(severity="critical")
        result = policy.score(event)
        assert result.base_score == SEVERITY_SCORES["critical"]

    def test_no_recurrence_bonus_for_first_occurrence(self):
        policy = PriorityPolicy()
        event = _make_event()
        result = policy.score(event, recurrence=1)
        assert result.recurrence_bonus == 0

    def test_recurrence_bonus_increases_with_count(self):
        policy = PriorityPolicy(recurrence_weight=5)
        event = _make_event()
        result = policy.score(event, recurrence=4)
        assert result.recurrence_bonus == 15

    def test_recurrence_bonus_capped(self):
        policy = PriorityPolicy(recurrence_weight=10, max_recurrence_bonus=20)
        event = _make_event()
        result = policy.score(event, recurrence=100)
        assert result.recurrence_bonus == 20

    def test_tag_bonus_applied_for_matching_tag(self):
        policy = PriorityPolicy(high_priority_tags=["critical_path"], tag_bonus=25)
        event = _make_event(tags=["critical_path"])
        result = policy.score(event)
        assert result.tag_bonus == 25

    def test_no_tag_bonus_when_no_match(self):
        policy = PriorityPolicy(high_priority_tags=["critical_path"])
        event = _make_event(tags=["other"])
        result = policy.score(event)
        assert result.tag_bonus == 0

    def test_pipeline_and_check_captured(self):
        policy = PriorityPolicy()
        event = _make_event(pipeline="my_pipe", check="null_check")
        result = policy.score(event)
        assert result.pipeline == "my_pipe"
        assert result.check == "null_check"
