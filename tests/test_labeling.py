"""Tests for pipewarden.labeling."""
from __future__ import annotations
import pytest
from unittest.mock import MagicMock
from pipewarden.labeling import (
    LabelSet, LabelRule, LabeledEvent, apply_labels, batch_label
)


def _make_event(pipeline="pipe_a", check="row_count", severity="warning"):
    rule = MagicMock()
    rule.pipeline = pipeline
    rule.severity = severity
    event = MagicMock()
    event.rule = rule
    event.check_name = check
    return event


class TestLabelSet:
    def test_add_and_get(self):
        ls = LabelSet()
        ls.add("env", "prod")
        assert ls.get("env") == "prod"

    def test_get_missing_returns_none(self):
        ls = LabelSet()
        assert ls.get("missing") is None

    def test_matches_true(self):
        ls = LabelSet()
        ls.add("team", "data")
        assert ls.matches("team", "data") is True

    def test_matches_false(self):
        ls = LabelSet()
        ls.add("team", "data")
        assert ls.matches("team", "infra") is False

    def test_empty_key_raises(self):
        ls = LabelSet()
        with pytest.raises(ValueError):
            ls.add("", "value")

    def test_str_contains_labels(self):
        ls = LabelSet()
        ls.add("env", "prod")
        assert "env=prod" in str(ls)


class TestLabelRule:
    def test_applies_to_no_constraints(self):
        rule = LabelRule(key="env", value="prod")
        event = _make_event()
        assert rule.applies_to(event) is True

    def test_applies_to_matching_pipeline(self):
        rule = LabelRule(key="env", value="prod", pipeline="pipe_a")
        assert rule.applies_to(_make_event(pipeline="pipe_a")) is True

    def test_rejects_wrong_pipeline(self):
        rule = LabelRule(key="env", value="prod", pipeline="pipe_b")
        assert rule.applies_to(_make_event(pipeline="pipe_a")) is False

    def test_applies_to_matching_severity(self):
        rule = LabelRule(key="tier", value="1", severity="critical")
        assert rule.applies_to(_make_event(severity="critical")) is True

    def test_rejects_wrong_severity(self):
        rule = LabelRule(key="tier", value="1", severity="critical")
        assert rule.applies_to(_make_event(severity="warning")) is False

    def test_str(self):
        rule = LabelRule(key="env", value="prod")
        assert "env=prod" in str(rule)


class TestApplyLabels:
    def test_applies_matching_rules(self):
        event = _make_event(pipeline="pipe_a", severity="critical")
        rules = [
            LabelRule("env", "prod", pipeline="pipe_a"),
            LabelRule("tier", "1", severity="critical"),
        ]
        labeled = apply_labels(event, rules)
        assert labeled.label_set.get("env") == "prod"
        assert labeled.label_set.get("tier") == "1"

    def test_skips_non_matching_rules(self):
        event = _make_event(pipeline="pipe_a")
        rules = [LabelRule("env", "prod", pipeline="pipe_b")]
        labeled = apply_labels(event, rules)
        assert labeled.label_set.get("env") is None

    def test_labeled_event_str(self):
        event = _make_event()
        labeled = apply_labels(event, [])
        assert "pipe_a" in str(labeled)


class TestBatchLabel:
    def test_returns_one_per_event(self):
        events = [_make_event(), _make_event(pipeline="pipe_b")]
        results = batch_label(events, [])
        assert len(results) == 2

    def test_labels_applied_per_event(self):
        events = [_make_event(pipeline="pipe_a"), _make_event(pipeline="pipe_b")]
        rules = [LabelRule("env", "prod", pipeline="pipe_a")]
        results = batch_label(events, rules)
        assert results[0].label_set.get("env") == "prod"
        assert results[1].label_set.get("env") is None
