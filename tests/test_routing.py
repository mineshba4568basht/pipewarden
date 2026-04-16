"""Tests for pipewarden.routing."""
import pytest
from unittest.mock import MagicMock

from pipewarden.routing import RoutingRule, RoutingResult, AlertRouter


def _make_event(pipeline="pipe_a", severity="warning", check="row_count", tags=None):
    rule = MagicMock()
    rule.pipeline = pipeline
    rule.severity = severity
    rule.tags = tags or []
    result = MagicMock()
    result.check_name = check
    result.passed = False
    event = MagicMock()
    event.rule = rule
    event.result = result
    return event


class TestRoutingRule:
    def test_matches_no_constraints(self):
        rule = RoutingRule(channel="all")
        assert rule.matches(_make_event())

    def test_matches_pipeline(self):
        rule = RoutingRule(channel="c", pipeline="pipe_a")
        assert rule.matches(_make_event(pipeline="pipe_a"))
        assert not rule.matches(_make_event(pipeline="pipe_b"))

    def test_matches_severity(self):
        rule = RoutingRule(channel="c", severity="critical")
        assert rule.matches(_make_event(severity="critical"))
        assert not rule.matches(_make_event(severity="warning"))

    def test_matches_tags(self):
        rule = RoutingRule(channel="c", tags=["pii"])
        assert rule.matches(_make_event(tags=["pii", "finance"]))
        assert not rule.matches(_make_event(tags=["finance"]))

    def test_str_minimal(self):
        rule = RoutingRule(channel="slack")
        assert "slack" in str(rule)

    def test_str_full(self):
        rule = RoutingRule(channel="pagerduty", pipeline="p", severity="critical", tags=["pii"])
        s = str(rule)
        assert "pagerduty" in s
        assert "critical" in s


class TestRoutingResult:
    def test_routed_true(self):
        event = _make_event()
        r = RoutingResult(event=event, channels=["slack"])
        assert r.routed()

    def test_routed_false_when_empty(self):
        event = _make_event()
        r = RoutingResult(event=event, channels=[])
        assert not r.routed()

    def test_str_contains_status(self):
        event = _make_event()
        r = RoutingResult(event=event, channels=["slack"])
        assert "routed" in str(r)


class TestAlertRouter:
    def test_default_channel_when_no_rules_match(self):
        router = AlertRouter(rules=[], default_channel="fallback")
        result = router.route(_make_event())
        assert result.channels == ["fallback"]

    def test_matching_rule_returns_channel(self):
        rules = [RoutingRule(channel="slack", severity="critical")]
        router = AlertRouter(rules=rules)
        result = router.route(_make_event(severity="critical"))
        assert "slack" in result.channels

    def test_multiple_matching_rules(self):
        rules = [
            RoutingRule(channel="slack", pipeline="pipe_a"),
            RoutingRule(channel="email", severity="warning"),
        ]
        router = AlertRouter(rules=rules)
        result = router.route(_make_event(pipeline="pipe_a", severity="warning"))
        assert "slack" in result.channels
        assert "email" in result.channels

    def test_route_all_returns_one_per_event(self):
        router = AlertRouter(rules=[])
        events = [_make_event(), _make_event()]
        results = router.route_all(events)
        assert len(results) == 2
