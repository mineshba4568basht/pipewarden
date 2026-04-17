"""Tests for pipewarden.checkpoint."""
from __future__ import annotations
import json, pathlib
from datetime import datetime
import pytest
from pipewarden.checkpoint import CheckpointEntry, CheckpointStore


# --- CheckpointEntry ---

class TestCheckpointEntry:
    def test_str_contains_pipeline_and_check(self):
        e = CheckpointEntry(pipeline="pipe1", check_name="row_count", status="pass", value=100.0)
        assert "pipe1" in str(e)
        assert "row_count" in str(e)

    def test_str_contains_status_and_value(self):
        e = CheckpointEntry(pipeline="p", check_name="c", status="fail", value=42.5)
        assert "fail" in str(e)
        assert "42.5" in str(e)

    def test_recorded_at_set_automatically(self):
        before = datetime.utcnow()
        e = CheckpointEntry(pipeline="p", check_name="c", status="pass", value=1.0)
        assert e.recorded_at >= before

    def test_round_trip_dict(self):
        e = CheckpointEntry(pipeline="p", check_name="c", status="pass", value=7.0)
        assert CheckpointEntry.from_dict(e.to_dict()).value == 7.0


# --- CheckpointStore ---

@pytest.fixture
def store(tmp_path):
    return CheckpointStore(path=str(tmp_path / "cp.json"))


@pytest.fixture
def sample_entry():
    return CheckpointEntry(pipeline="pipe", check_name="nulls", status="pass", value=0.0)


class TestCheckpointStore:
    def test_empty_on_init(self, store):
        assert store.all_entries() == []

    def test_record_and_retrieve(self, store, sample_entry):
        store.record(sample_entry)
        assert len(store.all_entries()) == 1

    def test_latest_returns_most_recent(self, store):
        e1 = CheckpointEntry(pipeline="p", check_name="c", status="pass", value=1.0)
        e2 = CheckpointEntry(pipeline="p", check_name="c", status="fail", value=2.0)
        store.record(e1)
        store.record(e2)
        latest = store.latest("p", "c")
        assert latest.value == 2.0

    def test_latest_none_when_missing(self, store):
        assert store.latest("missing", "check") is None

    def test_limit_respected(self, store):
        for i in range(10):
            store.record(CheckpointEntry(pipeline="p", check_name="c", status="pass", value=float(i)))
        assert len(store.all_entries(limit=5)) == 5

    def test_clear_removes_all(self, store, sample_entry):
        store.record(sample_entry)
        removed = store.clear()
        assert removed == 1
        assert store.all_entries() == []

    def test_persists_to_disk(self, tmp_path):
        path = str(tmp_path / "cp.json")
        s1 = CheckpointStore(path=path)
        s1.record(CheckpointEntry(pipeline="p", check_name="c", status="pass", value=99.0))
        s2 = CheckpointStore(path=path)
        assert len(s2.all_entries()) == 1
        assert s2.all_entries()[0].value == 99.0
