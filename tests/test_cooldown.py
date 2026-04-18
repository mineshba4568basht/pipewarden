"""Tests for pipewarden.cooldown."""
from __future__ import annotations
import pytest
from datetime import datetime, timedelta
from pipewarden.cooldown import CooldownEntry, CooldownManager


def _dt(offset_seconds: int = 0) -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0) + timedelta(seconds=offset_seconds)


class TestCooldownEntry:
    def test_is_cooling_within_window(self):
        e = CooldownEntry("pipe", "check", _dt(), 300)
        assert e.is_cooling(_dt(100)) is True

    def test_is_not_cooling_after_window(self):
        e = CooldownEntry("pipe", "check", _dt(), 300)
        assert e.is_cooling(_dt(400)) is False

    def test_expires_at(self):
        e = CooldownEntry("pipe", "check", _dt(), 300)
        assert e.expires_at() == _dt(300)

    def test_str_cooling(self):
        e = CooldownEntry("pipe", "check", _dt(), 300)
        s = str(e)
        assert "cooling" in s or "ready" in s
        assert "pipe" in s


class TestCooldownManager:
    def test_default_cooldown(self):
        m = CooldownManager()
        assert m.default_cooldown == 300

    def test_invalid_cooldown_raises(self):
        with pytest.raises(ValueError):
            CooldownManager(default_cooldown=-1)

    def test_not_cooling_before_record(self):
        m = CooldownManager(60)
        assert m.is_cooling("pipe", "check") is False

    def test_cooling_after_record(self):
        m = CooldownManager(300)
        m.record("pipe", "check", now=_dt())
        assert m.is_cooling("pipe", "check", now=_dt(100)) is True

    def test_not_cooling_after_expiry(self):
        m = CooldownManager(300)
        m.record("pipe", "check", now=_dt())
        assert m.is_cooling("pipe", "check", now=_dt(400)) is False

    def test_clear_removes_entry(self):
        m = CooldownManager(300)
        m.record("pipe", "check", now=_dt())
        removed = m.clear("pipe", "check")
        assert removed is True
        assert m.is_cooling("pipe", "check", now=_dt(100)) is False

    def test_clear_missing_returns_false(self):
        m = CooldownManager()
        assert m.clear("pipe", "check") is False

    def test_all_entries_empty(self):
        m = CooldownManager()
        assert m.all_entries() == []

    def test_all_entries_returns_recorded(self):
        m = CooldownManager()
        m.record("p1", "c1", now=_dt())
        m.record("p2", "c2", now=_dt())
        assert len(m.all_entries()) == 2

    def test_independent_keys(self):
        m = CooldownManager(300)
        m.record("pipe", "check_a", now=_dt())
        assert m.is_cooling("pipe", "check_b", now=_dt(10)) is False
