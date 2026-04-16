"""Tests for pipewarden.suppression."""
from datetime import datetime, timedelta
import pytest
from pipewarden.suppression import SuppressionWindow, SuppressionManager


def _dt(offset_minutes: int = 0) -> datetime:
    return datetime.utcnow() + timedelta(minutes=offset_minutes)


# --- SuppressionWindow ---

class TestSuppressionWindow:
    def test_is_active_within_window(self):
        w = SuppressionWindow("pipe", _dt(-5), _dt(5))
        assert w.is_active()

    def test_is_inactive_before_window(self):
        w = SuppressionWindow("pipe", _dt(10), _dt(20))
        assert not w.is_active()

    def test_is_inactive_after_window(self):
        w = SuppressionWindow("pipe", _dt(-20), _dt(-5))
        assert not w.is_active()

    def test_covers_matching_pipeline(self):
        w = SuppressionWindow("pipe_a", _dt(-1), _dt(1))
        assert w.covers("pipe_a")

    def test_covers_rejects_other_pipeline(self):
        w = SuppressionWindow("pipe_a", _dt(-1), _dt(1))
        assert not w.covers("pipe_b")

    def test_str_contains_pipeline(self):
        w = SuppressionWindow("my_pipe", _dt(-1), _dt(1), reason="maintenance")
        s = str(w)
        assert "my_pipe" in s
        assert "ACTIVE" in s
        assert "maintenance" in s

    def test_str_shows_inactive(self):
        w = SuppressionWindow("my_pipe", _dt(-20), _dt(-10))
        assert "INACTIVE" in str(w)


# --- SuppressionManager ---

class TestSuppressionManager:
    def test_empty_manager_not_suppressed(self):
        mgr = SuppressionManager()
        assert not mgr.is_suppressed("pipe")

    def test_add_and_suppress(self):
        mgr = SuppressionManager()
        mgr.add(SuppressionWindow("pipe", _dt(-1), _dt(1)))
        assert mgr.is_suppressed("pipe")

    def test_other_pipeline_not_suppressed(self):
        mgr = SuppressionManager()
        mgr.add(SuppressionWindow("pipe_a", _dt(-1), _dt(1)))
        assert not mgr.is_suppressed("pipe_b")

    def test_active_windows_returns_only_active(self):
        mgr = SuppressionManager()
        mgr.add(SuppressionWindow("a", _dt(-1), _dt(1)))
        mgr.add(SuppressionWindow("b", _dt(-20), _dt(-10)))
        active = mgr.active_windows()
        assert len(active) == 1
        assert active[0].pipeline == "a"

    def test_remove_expired_clears_past_windows(self):
        mgr = SuppressionManager()
        mgr.add(SuppressionWindow("a", _dt(-20), _dt(-10)))
        mgr.add(SuppressionWindow("b", _dt(-1), _dt(1)))
        removed = mgr.remove_expired()
        assert removed == 1
        assert len(mgr) == 1

    def test_clear_removes_all(self):
        mgr = SuppressionManager()
        mgr.add(SuppressionWindow("a", _dt(-1), _dt(1)))
        mgr.clear()
        assert len(mgr) == 0

    def test_len_reflects_count(self):
        mgr = SuppressionManager()
        assert len(mgr) == 0
        mgr.add(SuppressionWindow("a", _dt(-1), _dt(1)))
        assert len(mgr) == 1
