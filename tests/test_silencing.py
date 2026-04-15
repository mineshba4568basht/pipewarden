"""Tests for pipewarden.silencing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.config import AlertRule
from pipewarden.runner import AlertEvent
from pipewarden.silencing import SilenceManager, SilenceRule


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(pipeline: str = "my_pipeline", check: str = "row_count") -> AlertEvent:
    rule = AlertRule(pipeline=pipeline, check=check, threshold=100)
    result = CheckResult(
        check_name=check,
        status=CheckStatus.FAIL,
        value=0,
        message="too low",
    )
    return AlertEvent(rule=rule, result=result)


FUTURE = datetime.now(timezone.utc) + timedelta(hours=1)
PAST = datetime.now(timezone.utc) - timedelta(hours=1)


# ---------------------------------------------------------------------------
# SilenceRule
# ---------------------------------------------------------------------------

class TestSilenceRule:
    def test_str_contains_pipeline_and_check(self):
        r = SilenceRule(pipeline="etl_*", check="row_count", reason="planned maintenance")
        s = str(r)
        assert "etl_*" in s
        assert "row_count" in s
        assert "planned maintenance" in s

    def test_no_expiry_is_always_active(self):
        r = SilenceRule(pipeline="p", expires_at=None)
        assert r.is_active() is True

    def test_future_expiry_is_active(self):
        r = SilenceRule(pipeline="p", expires_at=FUTURE)
        assert r.is_active() is True

    def test_past_expiry_is_inactive(self):
        r = SilenceRule(pipeline="p", expires_at=PAST)
        assert r.is_active() is False

    def test_glob_pipeline_matches(self):
        r = SilenceRule(pipeline="etl_*")
        event = _make_event(pipeline="etl_orders")
        assert r.matches(event) is True

    def test_glob_pipeline_no_match(self):
        r = SilenceRule(pipeline="etl_*")
        event = _make_event(pipeline="reporting")
        assert r.matches(event) is False

    def test_exact_check_match(self):
        r = SilenceRule(pipeline="*", check="row_count")
        event = _make_event(check="row_count")
        assert r.matches(event) is True

    def test_check_glob_mismatch(self):
        r = SilenceRule(pipeline="*", check="null_check")
        event = _make_event(check="row_count")
        assert r.matches(event) is False

    def test_expired_rule_does_not_match(self):
        r = SilenceRule(pipeline="*", check="*", expires_at=PAST)
        event = _make_event()
        assert r.matches(event) is False


# ---------------------------------------------------------------------------
# SilenceManager
# ---------------------------------------------------------------------------

class TestSilenceManager:
    def test_empty_manager_silences_nothing(self):
        mgr = SilenceManager()
        assert mgr.is_silenced(_make_event()) is False

    def test_matching_rule_silences_event(self):
        mgr = SilenceManager()
        mgr.add(SilenceRule(pipeline="my_pipeline", check="row_count"))
        assert mgr.is_silenced(_make_event()) is True

    def test_expired_rule_does_not_silence(self):
        mgr = SilenceManager()
        mgr.add(SilenceRule(pipeline="*", check="*", expires_at=PAST))
        assert mgr.is_silenced(_make_event()) is False

    def test_filter_events_removes_silenced(self):
        mgr = SilenceManager()
        mgr.add(SilenceRule(pipeline="my_pipeline"))
        events = [_make_event("my_pipeline"), _make_event("other_pipeline")]
        result = mgr.filter_events(events)
        assert len(result) == 1
        assert result[0].rule.pipeline == "other_pipeline"

    def test_filter_events_empty_list(self):
        mgr = SilenceManager()
        assert mgr.filter_events([]) == []

    def test_active_rules_excludes_expired(self):
        mgr = SilenceManager()
        mgr.add(SilenceRule(pipeline="a", expires_at=FUTURE))
        mgr.add(SilenceRule(pipeline="b", expires_at=PAST))
        active = mgr.active_rules()
        assert len(active) == 1
        assert active[0].pipeline == "a"
