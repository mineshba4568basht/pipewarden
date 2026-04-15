"""Tests for pipewarden.escalation."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from pipewarden.escalation import (
    EscalationPolicy,
    EscalationResult,
    evaluate_escalation,
    batch_evaluate,
    _count_consecutive_failures,
)
from pipewarden.history import HistoryEntry
from pipewarden.runner import AlertEvent


def _make_event(check_name: str) -> AlertEvent:
    rule = MagicMock()
    rule.name = check_name
    return AlertEvent(rule=rule, result=MagicMock(passed=False), pipeline="pipe")


def _make_entry(check_names: list[str]) -> HistoryEntry:
    entry = MagicMock(spec=HistoryEntry)
    entry.events = [_make_event(n) for n in check_names]
    return entry


@pytest.fixture
def policy() -> EscalationPolicy:
    return EscalationPolicy(pipeline="pipe", check_name="row_count", threshold=3)


@pytest.fixture
def store_factory():
    def _make(entries_per_run: list[list[str]]):
        store = MagicMock()
        store.load.return_value = [_make_entry(names) for names in entries_per_run]
        return store
    return _make


# ---------------------------------------------------------------------------
# EscalationPolicy construction
# ---------------------------------------------------------------------------

class TestEscalationPolicyConstruction:
    def test_valid_policy(self, policy):
        assert policy.threshold == 3
        assert policy.notify_every == 1

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            EscalationPolicy(pipeline="p", check_name="c", threshold=0)

    def test_invalid_notify_every_raises(self):
        with pytest.raises(ValueError, match="notify_every"):
            EscalationPolicy(pipeline="p", check_name="c", notify_every=0)

    def test_str_contains_pipeline_and_check(self, policy):
        s = str(policy)
        assert "pipe" in s
        assert "row_count" in s


# ---------------------------------------------------------------------------
# _count_consecutive_failures
# ---------------------------------------------------------------------------

class TestCountConsecutiveFailures:
    def test_empty_history_returns_zero(self, store_factory):
        store = store_factory([])
        assert _count_consecutive_failures(store, "pipe", "row_count") == 0

    def test_three_consecutive_failures(self, store_factory):
        store = store_factory([["row_count"], ["row_count"], ["row_count"]])
        assert _count_consecutive_failures(store, "pipe", "row_count") == 3

    def test_stops_at_non_failing_run(self, store_factory):
        store = store_factory([["row_count"], [], ["row_count"], ["row_count"]])
        assert _count_consecutive_failures(store, "pipe", "row_count") == 2


# ---------------------------------------------------------------------------
# evaluate_escalation
# ---------------------------------------------------------------------------

class TestEvaluateEscalation:
    def test_below_threshold_no_escalation(self, policy, store_factory):
        store = store_factory([["row_count"], ["row_count"]])
        result = evaluate_escalation(policy, store)
        assert not result.should_escalate
        assert result.consecutive_failures == 2

    def test_at_threshold_escalates(self, policy, store_factory):
        store = store_factory([["row_count"]] * 3)
        result = evaluate_escalation(policy, store)
        assert result.should_escalate

    def test_above_threshold_notify_every_1(self, policy, store_factory):
        store = store_factory([["row_count"]] * 5)
        result = evaluate_escalation(policy, store)
        assert result.should_escalate

    def test_notify_every_skips_intermediate(self, store_factory):
        p = EscalationPolicy(pipeline="pipe", check_name="row_count", threshold=2, notify_every=3)
        store = store_factory([["row_count"]] * 4)  # excess=2, 2 % 3 != 0
        result = evaluate_escalation(p, store)
        assert not result.should_escalate

    def test_notify_every_fires_on_boundary(self, store_factory):
        p = EscalationPolicy(pipeline="pipe", check_name="row_count", threshold=2, notify_every=3)
        store = store_factory([["row_count"]] * 5)  # excess=3, 3 % 3 == 0
        result = evaluate_escalation(p, store)
        assert result.should_escalate

    def test_result_str_contains_status(self, policy, store_factory):
        store = store_factory([["row_count"]] * 3)
        result = evaluate_escalation(policy, store)
        assert "ESCALATE" in str(result)


# ---------------------------------------------------------------------------
# batch_evaluate
# ---------------------------------------------------------------------------

def test_batch_evaluate_returns_one_result_per_policy(store_factory):
    store = store_factory([["row_count"]] * 3)
    policies = [
        EscalationPolicy(pipeline="pipe", check_name="row_count", threshold=3),
        EscalationPolicy(pipeline="pipe", check_name="null_check", threshold=2),
    ]
    results = batch_evaluate(policies, store)
    assert len(results) == 2
    assert all(isinstance(r, EscalationResult) for r in results)
