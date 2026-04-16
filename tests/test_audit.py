"""Tests for pipewarden.audit."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipewarden.audit import AuditEntry, AuditLog


@pytest.fixture
def store(tmp_path) -> AuditLog:
    return AuditLog(str(tmp_path / "audit.json"))


@pytest.fixture
def sample_entry() -> AuditEntry:
    return AuditEntry(
        pipeline="sales",
        check="row_count",
        status="fail",
        message="Expected >= 100, got 42",
        timestamp=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


class TestAuditEntry:
    def test_str_contains_pipeline_and_check(self, sample_entry):
        s = str(sample_entry)
        assert "sales" in s
        assert "row_count" in s

    def test_str_contains_status(self, sample_entry):
        assert "fail" in str(sample_entry)

    def test_roundtrip(self, sample_entry):
        restored = AuditEntry.from_dict(sample_entry.to_dict())
        assert restored.pipeline == sample_entry.pipeline
        assert restored.status == sample_entry.status
        assert restored.timestamp == sample_entry.timestamp


class TestAuditLog:
    def test_empty_on_new_file(self, store):
        assert store.entries() == []

    def test_record_persists(self, store, sample_entry, tmp_path):
        store.record(sample_entry)
        log2 = AuditLog(str(tmp_path / "audit.json"))
        assert len(log2.entries()) == 1

    def test_filter_by_pipeline(self, store):
        store.record(AuditEntry("pipe_a", "check1", "pass", "ok"))
        store.record(AuditEntry("pipe_b", "check1", "fail", "bad"))
        assert len(store.entries(pipeline="pipe_a")) == 1

    def test_limit_respected(self, store):
        for i in range(10):
            store.record(AuditEntry("p", "c", "pass", str(i)))
        assert len(store.entries(limit=3)) == 3

    def test_clear_removes_all(self, store, sample_entry):
        store.record(sample_entry)
        removed = store.clear()
        assert removed == 1
        assert store.entries() == []

    def test_corrupted_file_returns_empty(self, tmp_path):
        f = tmp_path / "audit.json"
        f.write_text("not json")
        log = AuditLog(str(f))
        assert log.entries() == []
