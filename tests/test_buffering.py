"""Tests for pipewarden.buffering."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from pipewarden.buffering import AlertBuffer, BufferPolicy, FlushResult
from pipewarden.runner import AlertEvent
from pipewarden.config import AlertRule


def _make_event(pipeline: str = "pipe", check: str = "row_count") -> AlertEvent:
    rule = AlertRule(name=check, check="row_count", threshold=0)
    return AlertEvent(pipeline=pipeline, rule=rule, observed_value=0)


# ---------------------------------------------------------------------------
# BufferPolicy
# ---------------------------------------------------------------------------

class TestBufferPolicy:
    def test_defaults(self):
        p = BufferPolicy()
        assert p.max_size == 50
        assert p.max_age_seconds == 300

    def test_invalid_max_size_raises(self):
        with pytest.raises(ValueError, match="max_size"):
            BufferPolicy(max_size=0)

    def test_invalid_max_age_raises(self):
        with pytest.raises(ValueError, match="max_age_seconds"):
            BufferPolicy(max_age_seconds=0)

    def test_str_contains_policy_fields(self):
        p = BufferPolicy(max_size=10, max_age_seconds=60)
        s = str(p)
        assert "10" in s
        assert "60" in s


# ---------------------------------------------------------------------------
# FlushResult
# ---------------------------------------------------------------------------

class TestFlushResult:
    def test_count_reflects_events(self):
        events = [_make_event() for _ in range(3)]
        r = FlushResult(flushed=events, reason="manual")
        assert r.count == 3

    def test_str_contains_count_and_reason(self):
        r = FlushResult(flushed=[_make_event()], reason="size")
        s = str(r)
        assert "1" in s
        assert "size" in s


# ---------------------------------------------------------------------------
# AlertBuffer
# ---------------------------------------------------------------------------

class TestAlertBuffer:
    def test_pending_starts_at_zero(self):
        buf = AlertBuffer()
        assert buf.pending == 0

    def test_add_increments_pending(self):
        buf = AlertBuffer(BufferPolicy(max_size=10))
        buf.add(_make_event())
        assert buf.pending == 1

    def test_no_flush_below_max_size(self):
        buf = AlertBuffer(BufferPolicy(max_size=5))
        for _ in range(4):
            result = buf.add(_make_event())
        assert result is None
        assert buf.pending == 4

    def test_flush_on_max_size(self):
        buf = AlertBuffer(BufferPolicy(max_size=3))
        result = None
        for _ in range(3):
            result = buf.add(_make_event())
        assert result is not None
        assert result.reason == "size"
        assert result.count == 3
        assert buf.pending == 0

    def test_manual_flush_returns_result(self):
        buf = AlertBuffer()
        buf.add(_make_event())
        result = buf.flush()
        assert result is not None
        assert result.reason == "manual"
        assert buf.pending == 0

    def test_manual_flush_empty_returns_none(self):
        buf = AlertBuffer()
        assert buf.flush() is None

    def test_check_age_triggers_flush(self):
        buf = AlertBuffer(BufferPolicy(max_age_seconds=10))
        buf.add(_make_event())
        old_time = datetime.now(timezone.utc) - timedelta(seconds=20)
        buf._opened_at = old_time
        result = buf.check_age()
        assert result is not None
        assert result.reason == "age"

    def test_check_age_no_flush_when_fresh(self):
        buf = AlertBuffer(BufferPolicy(max_age_seconds=300))
        buf.add(_make_event())
        assert buf.check_age() is None

    def test_check_age_empty_buffer_returns_none(self):
        buf = AlertBuffer()
        assert buf.check_age() is None

    def test_str_contains_pending(self):
        buf = AlertBuffer()
        buf.add(_make_event())
        assert "pending=1" in str(buf)
