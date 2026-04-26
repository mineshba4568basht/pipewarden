"""Tests for pipewarden.filtering."""
from __future__ import annotations

import pytest

from pipewarden.filtering import FilterChain, FilterResult, FilterRule
from pipewarden.runner import AlertEvent
from pipewarden.config import AlertRule


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_rule(name: str = "check_rows", severity: str = "warning") -> AlertRule:
    return AlertRule(name=name, check="row_count", threshold=100, severity=severity)


def _make_event(pipeline: str = "etl", severity: str = "warning") -> AlertEvent:
    rule = _make_rule(severity=severity)
    return AlertEvent(pipeline=pipeline, rule=rule, observed=50)


# ---------------------------------------------------------------------------
# FilterRule
# ---------------------------------------------------------------------------

class TestFilterRule:
    def test_str_contains_name_and_mode(self):
        rule = FilterRule(name="only_critical", predicate=lambda e: True, mode="include")
        assert "only_critical" in str(rule)
        assert "include" in str(rule)

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="mode"):
            FilterRule(name="bad", predicate=lambda e: True, mode="filter")

    def test_matches_delegates_to_predicate(self):
        event = _make_event()
        rule = FilterRule(name="always", predicate=lambda e: True)
        assert rule.matches(event) is True

    def test_exclude_mode_stored(self):
        rule = FilterRule(name="skip", predicate=lambda e: False, mode="exclude")
        assert rule.mode == "exclude"


# ---------------------------------------------------------------------------
# FilterResult
# ---------------------------------------------------------------------------

class TestFilterResult:
    def test_total_sums_both_lists(self):
        r = FilterResult(
            accepted=[_make_event()],
            rejected=[_make_event(), _make_event()],
        )
        assert r.total == 3

    def test_acceptance_rate_all_accepted(self):
        r = FilterResult(accepted=[_make_event(), _make_event()])
        assert r.acceptance_rate == 1.0

    def test_acceptance_rate_none_accepted(self):
        r = FilterResult(rejected=[_make_event()])
        assert r.acceptance_rate == 0.0

    def test_acceptance_rate_empty_is_one(self):
        r = FilterResult()
        assert r.acceptance_rate == 1.0

    def test_str_contains_counts(self):
        r = FilterResult(accepted=[_make_event()], rejected=[_make_event()])
        s = str(r)
        assert "accepted=1" in s
        assert "rejected=1" in s


# ---------------------------------------------------------------------------
# FilterChain
# ---------------------------------------------------------------------------

class TestFilterChain:
    def test_empty_chain_accepts_all(self):
        chain = FilterChain()
        events = [_make_event(), _make_event()]
        result = chain.apply(events)
        assert len(result.accepted) == 2
        assert len(result.rejected) == 0

    def test_include_rule_keeps_matching(self):
        chain = FilterChain()
        chain.add(FilterRule(
            name="critical_only",
            predicate=lambda e: e.rule.severity == "critical",
            mode="include",
        ))
        events = [
            _make_event(severity="critical"),
            _make_event(severity="warning"),
        ]
        result = chain.apply(events)
        assert len(result.accepted) == 1
        assert result.accepted[0].rule.severity == "critical"

    def test_exclude_rule_drops_matching(self):
        chain = FilterChain()
        chain.add(FilterRule(
            name="drop_etl",
            predicate=lambda e: e.pipeline == "etl",
            mode="exclude",
        ))
        events = [_make_event(pipeline="etl"), _make_event(pipeline="dbt")]
        result = chain.apply(events)
        assert len(result.accepted) == 1
        assert result.accepted[0].pipeline == "dbt"

    def test_len_returns_rule_count(self):
        chain = FilterChain()
        chain.add(FilterRule(name="r1", predicate=lambda e: True))
        chain.add(FilterRule(name="r2", predicate=lambda e: True))
        assert len(chain) == 2

    def test_str_contains_rule_count(self):
        chain = FilterChain()
        chain.add(FilterRule(name="r1", predicate=lambda e: True))
        assert "rules=1" in str(chain)

    def test_multiple_rules_all_must_pass(self):
        chain = FilterChain()
        chain.add(FilterRule(
            name="critical",
            predicate=lambda e: e.rule.severity == "critical",
            mode="include",
        ))
        chain.add(FilterRule(
            name="not_etl",
            predicate=lambda e: e.pipeline == "etl",
            mode="exclude",
        ))
        events = [
            _make_event(pipeline="etl", severity="critical"),
            _make_event(pipeline="dbt", severity="critical"),
            _make_event(pipeline="dbt", severity="warning"),
        ]
        result = chain.apply(events)
        assert len(result.accepted) == 1
        assert result.accepted[0].pipeline == "dbt"
