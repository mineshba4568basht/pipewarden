"""Tests for pipewarden.shadowing."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from pipewarden.shadowing import ShadowRecord, ShadowPolicy, ShadowManager


def _make_event(pipeline: str = "pipe_a", check: str = "row_count", severity: str = "warning"):
    rule = MagicMock()
    rule.severity = severity
    rule.enabled = True
    event = MagicMock()
    event.pipeline = pipeline
    event.check_name = check
    event.rule = rule
    return event


# ---------------------------------------------------------------------------
# ShadowRecord
# ---------------------------------------------------------------------------

class TestShadowRecord:
    def test_str_would_alert(self):
        rec = ShadowRecord(pipeline="p", check="c", would_alert=True, severity="critical")
        assert "WOULD ALERT" in str(rec)
        assert "p/c" in str(rec)

    def test_str_silent(self):
        rec = ShadowRecord(pipeline="p", check="c", would_alert=False, severity="warning")
        assert "silent" in str(rec)

    def test_recorded_at_set_automatically(self):
        rec = ShadowRecord(pipeline="p", check="c", would_alert=True, severity="info")
        assert isinstance(rec.recorded_at, datetime)


# ---------------------------------------------------------------------------
# ShadowPolicy
# ---------------------------------------------------------------------------

class TestShadowPolicy:
    def test_defaults(self):
        p = ShadowPolicy()
        assert p.enabled is True
        assert p.log_silent is False

    def test_custom_values(self):
        p = ShadowPolicy(enabled=False, log_silent=True)
        assert p.enabled is False
        assert p.log_silent is True

    def test_invalid_enabled_raises(self):
        with pytest.raises(TypeError):
            ShadowPolicy(enabled="yes")  # type: ignore[arg-type]

    def test_str_contains_enabled(self):
        p = ShadowPolicy()
        assert "enabled=True" in str(p)


# ---------------------------------------------------------------------------
# ShadowManager
# ---------------------------------------------------------------------------

class TestShadowManager:
    def test_evaluate_records_event(self):
        mgr = ShadowManager()
        event = _make_event()
        rec = mgr.evaluate(event)
        assert rec.would_alert is True
        assert len(mgr.records()) == 1

    def test_records_filtered_by_pipeline(self):
        mgr = ShadowManager()
        mgr.evaluate(_make_event(pipeline="a"))
        mgr.evaluate(_make_event(pipeline="b"))
        assert len(mgr.records(pipeline="a")) == 1
        assert len(mgr.records(pipeline="b")) == 1

    def test_clear_removes_all(self):
        mgr = ShadowManager()
        mgr.evaluate(_make_event())
        mgr.evaluate(_make_event())
        removed = mgr.clear()
        assert removed == 2
        assert mgr.records() == []

    def test_summary_counts(self):
        mgr = ShadowManager()
        mgr.evaluate(_make_event())
        mgr.evaluate(_make_event())
        s = mgr.summary()
        assert "2 evaluated" in s
        assert "2 would-alert" in s

    def test_policy_stored(self):
        policy = ShadowPolicy(log_silent=True)
        mgr = ShadowManager(policy=policy)
        assert mgr.policy.log_silent is True
