"""Tests for pipewarden.debounce."""
import pytest
from unittest.mock import MagicMock
from pipewarden.debounce import DebouncePolicy, DebounceManager, DebounceRecord


def _make_event(pipeline: str, check: str, passed: bool):
    rule = MagicMock()
    rule.pipeline = pipeline
    result = MagicMock()
    result.check_name = check
    result.passed = passed
    event = MagicMock()
    event.rule = rule
    event.result = result
    return event


class TestDebouncePolicy:
    def test_default_threshold(self):
        p = DebouncePolicy()
        assert p.threshold == 2

    def test_custom_threshold(self):
        p = DebouncePolicy(threshold=3)
        assert p.threshold == 3

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError):
            DebouncePolicy(threshold=0)

    def test_str(self):
        assert "2" in str(DebouncePolicy())


class TestDebounceRecord:
    def test_str(self):
        r = DebounceRecord(pipeline="p", check="c", consecutive_failures=3)
        assert "p" in str(r)
        assert "3" in str(r)


class TestDebounceManager:
    @pytest.fixture
    def manager(self):
        return DebounceManager(policy=DebouncePolicy(threshold=2))

    def test_passing_event_does_not_fire(self, manager):
        event = _make_event("p", "c", passed=True)
        assert manager.should_fire(event) is False

    def test_single_failure_below_threshold(self, manager):
        event = _make_event("p", "c", passed=False)
        assert manager.should_fire(event) is False

    def test_second_failure_meets_threshold(self, manager):
        event = _make_event("p", "c", passed=False)
        manager.should_fire(event)
        assert manager.should_fire(event) is True

    def test_pass_resets_counter(self, manager):
        fail = _make_event("p", "c", passed=False)
        ok = _make_event("p", "c", passed=True)
        manager.should_fire(fail)
        manager.should_fire(fail)
        manager.should_fire(ok)
        assert manager.record_for("p", "c") is None
        assert manager.should_fire(fail) is False

    def test_reset_clears_record(self, manager):
        event = _make_event("p", "c", passed=False)
        manager.should_fire(event)
        manager.reset("p", "c")
        assert manager.record_for("p", "c") is None

    def test_independent_pipelines(self, manager):
        e1 = _make_event("p1", "c", passed=False)
        e2 = _make_event("p2", "c", passed=False)
        manager.should_fire(e1)
        manager.should_fire(e1)
        assert manager.should_fire(e2) is False
