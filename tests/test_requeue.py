"""Tests for pipewarden.requeue."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pipewarden.requeue import RequeueEntry, RequeueStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(pipeline: str = "orders", check: str = "row_count", severity: str = "warning"):
    rule = MagicMock()
    rule.pipeline = pipeline
    rule.severity = severity
    result = MagicMock()
    result.check_name = check
    result.__str__ = lambda self: f"{check} failed"
    event = MagicMock()
    event.rule = rule
    event.result = result
    return event


@pytest.fixture()
def store(tmp_path: Path) -> RequeueStore:
    return RequeueStore(path=str(tmp_path / "requeue.json"))


# ---------------------------------------------------------------------------
# RequeueEntry
# ---------------------------------------------------------------------------

class TestRequeueEntry:
    def test_str_contains_pipeline_and_check(self):
        entry = RequeueEntry(pipeline="sales", check_name="null_check", severity="critical", reason="x")
        assert "sales" in str(entry)
        assert "null_check" in str(entry)

    def test_str_contains_attempts(self):
        entry = RequeueEntry(pipeline="a", check_name="b", severity="warning", reason="r", attempts=5)
        assert "attempts=5" in str(entry)

    def test_queued_at_set_automatically(self):
        before = datetime.now(timezone.utc)
        entry = RequeueEntry(pipeline="p", check_name="c", severity="info", reason="r")
        after = datetime.now(timezone.utc)
        assert before <= entry.queued_at <= after

    def test_round_trip_dict(self):
        entry = RequeueEntry(pipeline="etl", check_name="freshness", severity="critical", reason="stale", attempts=2)
        restored = RequeueEntry.from_dict(entry.to_dict())
        assert restored.pipeline == entry.pipeline
        assert restored.check_name == entry.check_name
        assert restored.attempts == entry.attempts
        assert restored.last_attempted_at is None

    def test_round_trip_with_last_attempted(self):
        entry = RequeueEntry(pipeline="etl", check_name="c", severity="warning", reason="r")
        entry.last_attempted_at = datetime.now(timezone.utc)
        restored = RequeueEntry.from_dict(entry.to_dict())
        assert restored.last_attempted_at is not None


# ---------------------------------------------------------------------------
# RequeueStore
# ---------------------------------------------------------------------------

class TestRequeueStore:
    def test_initially_empty(self, store: RequeueStore):
        assert store.all() == []

    def test_enqueue_adds_entry(self, store: RequeueStore):
        event = _make_event()
        entry = store.enqueue(event)
        assert len(store.all()) == 1
        assert entry.pipeline == "orders"

    def test_enqueue_persists_to_disk(self, tmp_path: Path):
        path = tmp_path / "rq.json"
        s = RequeueStore(path=str(path))
        s.enqueue(_make_event())
        data = json.loads(path.read_text())
        assert len(data) == 1
        assert data[0]["pipeline"] == "orders"

    def test_mark_attempted_increments(self, store: RequeueStore):
        entry = store.enqueue(_make_event())
        store.mark_attempted(entry)
        assert entry.attempts == 1
        assert entry.last_attempted_at is not None

    def test_remove_deletes_entry(self, store: RequeueStore):
        entry = store.enqueue(_make_event())
        store.remove(entry)
        assert store.all() == []

    def test_pending_filters_by_max_attempts(self, store: RequeueStore):
        e1 = store.enqueue(_make_event(pipeline="a"))
        e2 = store.enqueue(_make_event(pipeline="b"))
        store.mark_attempted(e1)
        store.mark_attempted(e1)
        store.mark_attempted(e1)  # attempts == 3
        pending = store.pending(max_attempts=3)
        assert e1 not in pending
        assert e2 in pending

    def test_clear_removes_all(self, store: RequeueStore):
        store.enqueue(_make_event())
        store.enqueue(_make_event())
        removed = store.clear()
        assert removed == 2
        assert store.all() == []

    def test_load_from_existing_file(self, tmp_path: Path):
        path = tmp_path / "rq.json"
        s1 = RequeueStore(path=str(path))
        s1.enqueue(_make_event(pipeline="pipe1"))
        s2 = RequeueStore(path=str(path))
        assert len(s2.all()) == 1
        assert s2.all()[0].pipeline == "pipe1"
