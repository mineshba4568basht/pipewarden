"""Tests for pipewarden.compaction."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from pipewarden.compaction import (
    CompactionPolicy,
    CompactionResult,
    _dedupe,
    compact,
)
from pipewarden.history import HistoryEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(
    pipeline: str = "pipe",
    check: str = "row_count",
    passed: bool = True,
    offset_seconds: int = 0,
) -> HistoryEntry:
    return HistoryEntry(
        pipeline=pipeline,
        check_name=check,
        passed=passed,
        value=100.0,
        recorded_at=_BASE + timedelta(seconds=offset_seconds),
    )


# ---------------------------------------------------------------------------
# CompactionPolicy
# ---------------------------------------------------------------------------


class TestCompactionPolicy:
    def test_defaults(self):
        p = CompactionPolicy()
        assert p.max_entries == 1000
        assert p.keep_failures is True
        assert p.dedupe_window_seconds == 60

    def test_invalid_max_entries_raises(self):
        with pytest.raises(ValueError, match="max_entries"):
            CompactionPolicy(max_entries=0)

    def test_invalid_dedupe_window_raises(self):
        with pytest.raises(ValueError, match="dedupe_window_seconds"):
            CompactionPolicy(dedupe_window_seconds=-1)

    def test_str_contains_max_entries(self):
        p = CompactionPolicy(max_entries=500)
        assert "500" in str(p)


# ---------------------------------------------------------------------------
# CompactionResult
# ---------------------------------------------------------------------------


class TestCompactionResult:
    def test_reduction_pct_zero_when_none_removed(self):
        r = CompactionResult(original_count=10, retained_count=10, removed_count=0)
        assert r.reduction_pct == 0.0

    def test_reduction_pct_calculated(self):
        r = CompactionResult(original_count=100, retained_count=75, removed_count=25)
        assert r.reduction_pct == 25.0

    def test_reduction_pct_zero_when_no_original(self):
        r = CompactionResult(original_count=0, retained_count=0, removed_count=0)
        assert r.reduction_pct == 0.0

    def test_str_contains_counts(self):
        r = CompactionResult(original_count=50, retained_count=40, removed_count=10)
        s = str(r)
        assert "50" in s
        assert "40" in s
        assert "10" in s


# ---------------------------------------------------------------------------
# _dedupe
# ---------------------------------------------------------------------------


class TestDedupe:
    def test_empty_returns_empty(self):
        assert _dedupe([], 60) == []

    def test_single_entry_returned(self):
        e = _entry()
        assert _dedupe([e], 60) == [e]

    def test_duplicate_passes_within_window_removed(self):
        e1 = _entry(offset_seconds=0)
        e2 = _entry(offset_seconds=30)
        result = _dedupe([e1, e2], window_seconds=60)
        assert len(result) == 1

    def test_passes_outside_window_kept(self):
        e1 = _entry(offset_seconds=0)
        e2 = _entry(offset_seconds=120)
        result = _dedupe([e1, e2], window_seconds=60)
        assert len(result) == 2

    def test_failures_never_deduped(self):
        e1 = _entry(passed=False, offset_seconds=0)
        e2 = _entry(passed=False, offset_seconds=10)
        result = _dedupe([e1, e2], window_seconds=60)
        assert len(result) == 2

    def test_different_pipelines_not_deduped(self):
        e1 = _entry(pipeline="pipe_a", offset_seconds=0)
        e2 = _entry(pipeline="pipe_b", offset_seconds=10)
        result = _dedupe([e1, e2], window_seconds=60)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# compact
# ---------------------------------------------------------------------------


class TestCompact:
    def _make_store(self, entries):
        store = MagicMock()
        store.recent.return_value = entries
        store._entries = list(entries)
        return store

    def test_removes_excess_entries(self):
        entries = [_entry(offset_seconds=i) for i in range(20)]
        store = self._make_store(entries)
        policy = CompactionPolicy(max_entries=10, dedupe_window_seconds=0)
        result = compact(store, policy)
        assert result.original_count == 20
        assert result.retained_count == 10
        assert result.removed_count == 10

    def test_keep_failures_preserves_failed_entries(self):
        passes = [_entry(passed=True, offset_seconds=i) for i in range(10)]
        failures = [_entry(passed=False, offset_seconds=i + 100) for i in range(5)]
        store = self._make_store(passes + failures)
        policy = CompactionPolicy(max_entries=5, keep_failures=True, dedupe_window_seconds=0)
        result = compact(store, policy)
        retained = store._entries
        assert all(not e.passed for e in retained if e.recorded_at.second >= 100)
        assert result.retained_count <= 10

    def test_no_removal_when_under_limit(self):
        entries = [_entry(offset_seconds=i * 120) for i in range(5)]
        store = self._make_store(entries)
        policy = CompactionPolicy(max_entries=100, dedupe_window_seconds=0)
        result = compact(store, policy)
        assert result.removed_count == 0
        assert result.retained_count == 5
