"""Tests for pipewarden.batching."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest
from pipewarden.batching import BatchPolicy, BatchRecord, BatchManager


def _make_event(pipeline: str = "pipe_a") -> MagicMock:
    event = MagicMock()
    event.rule.pipeline = pipeline
    return event


# --- BatchPolicy ---

class TestBatchPolicy:
    def test_defaults(self):
        p = BatchPolicy()
        assert p.max_size == 10
        assert p.max_age_seconds == 60.0

    def test_invalid_max_size_raises(self):
        with pytest.raises(ValueError):
            BatchPolicy(max_size=0)

    def test_invalid_max_age_raises(self):
        with pytest.raises(ValueError):
            BatchPolicy(max_age_seconds=0)

    def test_should_flush_on_size(self):
        p = BatchPolicy(max_size=2)
        r = BatchRecord(pipeline="p")
        r.events = [_make_event(), _make_event()]
        assert p.should_flush(r) is True

    def test_should_not_flush_below_size_and_age(self):
        p = BatchPolicy(max_size=5, max_age_seconds=60)
        r = BatchRecord(pipeline="p")
        r.events = [_make_event()]
        assert p.should_flush(r) is False

    def test_should_flush_on_age(self):
        p = BatchPolicy(max_size=10, max_age_seconds=1)
        r = BatchRecord(pipeline="p")
        r.created_at = datetime.now(timezone.utc) - timedelta(seconds=5)
        assert p.should_flush(r) is True


# --- BatchRecord ---

class TestBatchRecord:
    def test_size(self):
        r = BatchRecord(pipeline="p", events=[_make_event(), _make_event()])
        assert r.size == 2

    def test_is_flushed_false(self):
        r = BatchRecord(pipeline="p")
        assert r.is_flushed is False

    def test_is_flushed_true(self):
        r = BatchRecord(pipeline="p", flushed_at=datetime.now(timezone.utc))
        assert r.is_flushed is True

    def test_str_pending(self):
        r = BatchRecord(pipeline="p")
        assert "pending" in str(r)
        assert "p" in str(r)

    def test_str_flushed(self):
        r = BatchRecord(pipeline="p", flushed_at=datetime.now(timezone.utc))
        assert "flushed" in str(r)


# --- BatchManager ---

class TestBatchManager:
    def test_add_does_not_flush_below_threshold(self):
        m = BatchManager(BatchPolicy(max_size=5))
        result = m.add(_make_event("p"))
        assert result is None
        assert len(m.pending()) == 1

    def test_add_flushes_at_threshold(self):
        m = BatchManager(BatchPolicy(max_size=2))
        m.add(_make_event("p"))
        result = m.add(_make_event("p"))
        assert result is not None
        assert result.size == 2
        assert result.is_flushed

    def test_flush_removes_from_pending(self):
        m = BatchManager()
        m.add(_make_event("p"))
        m.flush("p")
        assert len(m.pending()) == 0

    def test_flush_all(self):
        m = BatchManager()
        m.add(_make_event("a"))
        m.add(_make_event("b"))
        flushed = m.flush_all()
        assert len(flushed) == 2
        assert len(m.pending()) == 0

    def test_flush_unknown_pipeline_returns_none(self):
        m = BatchManager()
        assert m.flush("nonexistent") is None
