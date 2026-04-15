"""Tests for pipewarden.schedule."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from pipewarden.schedule import CronSchedule, parse_schedule


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dt(minute: int = 0, hour: int = 0, day: int = 1, month: int = 1, weekday: int = 0) -> datetime:
    """Build a UTC datetime with the given components (weekday ignored by datetime constructor)."""
    # Use a known Monday (2024-01-01 is a Monday)
    base = datetime(2024, month, day, hour, minute, tzinfo=timezone.utc)
    return base


# ---------------------------------------------------------------------------
# CronSchedule construction
# ---------------------------------------------------------------------------

class TestCronScheduleConstruction:
    def test_valid_expression(self):
        s = CronSchedule("0 * * * *")
        assert s.expression == "0 * * * *"

    def test_alias_hourly(self):
        s = CronSchedule("@hourly")
        assert len(s._fields) == 5

    def test_alias_daily(self):
        s = CronSchedule("@daily")
        assert s._fields == ["0", "0", "*", "*", "*"]

    def test_invalid_expression_raises(self):
        with pytest.raises(ValueError, match="expected 5 fields"):
            CronSchedule("* * *")

    def test_str_representation(self):
        s = CronSchedule("*/10 * * * *")
        assert "*/10" in str(s)


# ---------------------------------------------------------------------------
# Field matching
# ---------------------------------------------------------------------------

class TestFieldMatches:
    def setup_method(self):
        self.s = CronSchedule("* * * * *")

    def test_wildcard_always_matches(self):
        assert self.s._field_matches(42, "*") is True

    def test_exact_match(self):
        assert self.s._field_matches(5, "5") is True
        assert self.s._field_matches(5, "6") is False

    def test_step_match(self):
        assert self.s._field_matches(10, "*/5") is True
        assert self.s._field_matches(7, "*/5") is False

    def test_range_match(self):
        assert self.s._field_matches(3, "1-5") is True
        assert self.s._field_matches(6, "1-5") is False

    def test_unsupported_syntax_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            self.s._field_matches(1, "1,2,3")


# ---------------------------------------------------------------------------
# is_due
# ---------------------------------------------------------------------------

class TestIsDue:
    def test_every_minute_always_due(self):
        s = parse_schedule("* * * * *")
        assert s.is_due(at=_dt(minute=37, hour=14)) is True

    def test_hourly_due_at_minute_zero(self):
        s = parse_schedule("@hourly")
        assert s.is_due(at=_dt(minute=0, hour=9)) is True
        assert s.is_due(at=_dt(minute=1, hour=9)) is False

    def test_daily_due_at_midnight(self):
        s = parse_schedule("@daily")
        assert s.is_due(at=_dt(minute=0, hour=0)) is True
        assert s.is_due(at=_dt(minute=0, hour=1)) is False

    def test_step_expression(self):
        s = parse_schedule("*/15 * * * *")
        assert s.is_due(at=_dt(minute=0)) is True
        assert s.is_due(at=_dt(minute=15)) is True
        assert s.is_due(at=_dt(minute=30)) is True
        assert s.is_due(at=_dt(minute=7)) is False

    def test_uses_now_when_at_is_none(self):
        """Smoke test: calling without 'at' should not raise."""
        s = parse_schedule("* * * * *")
        result = s.is_due()
        assert isinstance(result, bool)
