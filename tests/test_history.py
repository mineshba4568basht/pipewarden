"""Tests for pipewarden.history module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pipewarden.history import HistoryEntry, HistoryStore, make_entry


@pytest.fixture()
def store(tmp_path: Path) -> HistoryStore:
    return HistoryStore(path=tmp_path / "history.json")


@pytest.fixture()
def sample_entry() -> HistoryEntry:
    return HistoryEntry(
        run_id="abc-123",
        timestamp="2024-01-15T10:00:00",
        config_path="pipewarden.yaml",
        passed=True,
        total_checks=5,
        failed_checks=0,
        alert_count=0,
    )


class TestHistoryEntry:
    def test_str_pass(self, sample_entry: HistoryEntry) -> None:
        result = str(sample_entry)
        assert "PASS" in result
        assert "checks=5" in result
        assert "abc-123" in result

    def test_str_fail(self, sample_entry: HistoryEntry) -> None:
        sample_entry.passed = False
        sample_entry.failed_checks = 2
        result = str(sample_entry)
        assert "FAIL" in result
        assert "failed=2" in result


class TestHistoryStore:
    def test_load_empty_when_no_file(self, store: HistoryStore) -> None:
        assert store.load() == []

    def test_append_and_load(self, store: HistoryStore, sample_entry: HistoryEntry) -> None:
        store.append(sample_entry)
        entries = store.load()
        assert len(entries) == 1
        assert entries[0].run_id == "abc-123"

    def test_multiple_entries_newest_first(self, store: HistoryStore) -> None:
        for i in range(3):
            e = HistoryEntry(
                run_id=f"run-{i}",
                timestamp=f"2024-01-1{i}T00:00:00",
                config_path="cfg.yaml",
                passed=True,
                total_checks=1,
                failed_checks=0,
                alert_count=0,
            )
            store.append(e)
        entries = store.load()
        assert entries[0].run_id == "run-2"
        assert entries[-1].run_id == "run-0"

    def test_load_with_limit(self, store: HistoryStore, sample_entry: HistoryEntry) -> None:
        for _ in range(5):
            store.append(sample_entry)
        assert len(store.load(limit=3)) == 3

    def test_clear_removes_file(self, store: HistoryStore, sample_entry: HistoryEntry) -> None:
        store.append(sample_entry)
        store.clear()
        assert not store.path.exists()

    def test_clear_no_file_is_safe(self, store: HistoryStore) -> None:
        store.clear()  # should not raise

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "history.json"
        s = HistoryStore(path=nested)
        entry = HistoryEntry("x", "2024-01-01T00:00:00", "c.yaml", True, 1, 0, 0)
        s.append(entry)
        assert nested.exists()


class TestMakeEntry:
    def test_make_entry_fields(self) -> None:
        report = MagicMock()
        report.passed = False
        report.results = [MagicMock()] * 4
        report.failed_checks = [MagicMock()] * 2
        report.alert_events = [MagicMock()]
        entry = make_entry("run-99", "my_config.yaml", report)
        assert entry.run_id == "run-99"
        assert entry.config_path == "my_config.yaml"
        assert not entry.passed
        assert entry.total_checks == 4
        assert entry.failed_checks == 2
        assert entry.alert_count == 1
