"""Tests for pipewarden.retention."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pipewarden.history import HistoryEntry, HistoryStore
from pipewarden.retention import RetentionPolicy, PruneResult, apply_retention


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(hours_ago: float, pipeline: str = "pipe") -> HistoryEntry:
    ts = datetime.now(tz=timezone.utc) - timedelta(hours=hours_ago)
    return HistoryEntry(pipeline=pipeline, passed=True, timestamp=ts, checks_run=1, checks_failed=0)


@pytest.fixture()
def store(tmp_path: Path) -> HistoryStore:
    return HistoryStore(path=tmp_path / "history.json")


# ---------------------------------------------------------------------------
# RetentionPolicy
# ---------------------------------------------------------------------------

class TestRetentionPolicy:
    def test_defaults(self) -> None:
        p = RetentionPolicy()
        assert p.max_age_hours == 168
        assert p.max_entries == 1000

    def test_invalid_age_raises(self) -> None:
        with pytest.raises(ValueError, match="max_age_hours"):
            RetentionPolicy(max_age_hours=0)

    def test_invalid_entries_raises(self) -> None:
        with pytest.raises(ValueError, match="max_entries"):
            RetentionPolicy(max_entries=-1)

    def test_str(self) -> None:
        p = RetentionPolicy(max_age_hours=24, max_entries=100)
        assert "24" in str(p)
        assert "100" in str(p)


# ---------------------------------------------------------------------------
# PruneResult
# ---------------------------------------------------------------------------

class TestPruneResult:
    def test_total_removed(self) -> None:
        r = PruneResult(removed_by_age=3, removed_by_cap=2, remaining=5)
        assert r.total_removed == 5

    def test_str_contains_counts(self) -> None:
        r = PruneResult(removed_by_age=1, removed_by_cap=2, remaining=7)
        s = str(r)
        assert "removed=3" in s
        assert "remaining=7" in s


# ---------------------------------------------------------------------------
# apply_retention
# ---------------------------------------------------------------------------

class TestApplyRetention:
    def test_removes_old_entries(self, store: HistoryStore) -> None:
        store.save([_entry(200), _entry(100), _entry(1)])
        policy = RetentionPolicy(max_age_hours=168)
        result = apply_retention(store, policy)
        assert result.removed_by_age == 1
        assert result.remaining == 2

    def test_enforces_entry_cap(self, store: HistoryStore) -> None:
        entries = [_entry(i) for i in range(10, 0, -1)]  # 10 recent entries
        store.save(entries)
        policy = RetentionPolicy(max_age_hours=168, max_entries=5)
        result = apply_retention(store, policy)
        assert result.removed_by_cap == 5
        assert result.remaining == 5

    def test_no_entries_to_remove(self, store: HistoryStore) -> None:
        store.save([_entry(1), _entry(2)])
        policy = RetentionPolicy(max_age_hours=168, max_entries=1000)
        result = apply_retention(store, policy)
        assert result.total_removed == 0
        assert result.remaining == 2

    def test_empty_store(self, store: HistoryStore) -> None:
        policy = RetentionPolicy()
        result = apply_retention(store, policy)
        assert result.total_removed == 0
        assert result.remaining == 0

    def test_persists_after_prune(self, store: HistoryStore) -> None:
        store.save([_entry(200), _entry(1)])
        policy = RetentionPolicy(max_age_hours=168)
        apply_retention(store, policy)
        reloaded = store.load()
        assert len(reloaded) == 1
