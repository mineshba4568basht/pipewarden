"""Tests for pipewarden.trend."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipewarden.history import HistoryEntry, HistoryStore
from pipewarden.trend import TrendSummary, analyse_trend, _consecutive_failures


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(status: str, ts: str = "2024-01-01T00:00:00+00:00") -> HistoryEntry:
    return HistoryEntry(timestamp=ts, status=status, total=5, passed=3, failed=2)


@pytest.fixture()
def empty_store(tmp_path: Path) -> HistoryStore:
    return HistoryStore(path=str(tmp_path / "history.json"))


@pytest.fixture()
def populated_store(tmp_path: Path) -> HistoryStore:
    store = HistoryStore(path=str(tmp_path / "history.json"))
    for status in ["PASS", "PASS", "FAIL", "PASS", "FAIL", "FAIL"]:
        store.append(_entry(status))
    return store


# ---------------------------------------------------------------------------
# TrendSummary.__str__
# ---------------------------------------------------------------------------

class TestTrendSummaryStr:
    def test_str_contains_pass_rate(self):
        ts = TrendSummary(10, 8, 2, 0.8, 0, "PASS")
        assert "80%" in str(ts)

    def test_str_contains_consecutive_failures(self):
        ts = TrendSummary(5, 3, 2, 0.6, 2, "FAIL")
        assert "consecutive_failures=2" in str(ts)

    def test_str_unknown_last_status(self):
        ts = TrendSummary(0, 0, 0, 0.0, 0, None)
        assert "unknown" in str(ts)


# ---------------------------------------------------------------------------
# _consecutive_failures
# ---------------------------------------------------------------------------

class TestConsecutiveFailures:
    def test_no_entries(self):
        assert _consecutive_failures([]) == 0

    def test_all_pass(self):
        entries = [_entry("PASS")] * 4
        assert _consecutive_failures(entries) == 0

    def test_trailing_failures(self):
        entries = [_entry("PASS"), _entry("FAIL"), _entry("FAIL")]
        assert _consecutive_failures(entries) == 2

    def test_failure_then_pass_resets(self):
        entries = [_entry("FAIL"), _entry("FAIL"), _entry("PASS")]
        assert _consecutive_failures(entries) == 0


# ---------------------------------------------------------------------------
# analyse_trend
# ---------------------------------------------------------------------------

class TestAnalyseTrend:
    def test_empty_store_returns_zero_summary(self, empty_store: HistoryStore):
        summary = analyse_trend(empty_store)
        assert summary.total_runs == 0
        assert summary.pass_rate == 0.0
        assert summary.last_status is None

    def test_pass_rate_calculation(self, populated_store: HistoryStore):
        # 6 entries: 3 PASS, 3 FAIL  → 50 %
        summary = analyse_trend(populated_store, limit=20)
        assert summary.total_runs == 6
        assert summary.passed_runs == 3
        assert summary.failed_runs == 3
        assert abs(summary.pass_rate - 0.5) < 1e-9

    def test_consecutive_failures_at_tail(self, populated_store: HistoryStore):
        # Last two entries are FAIL
        summary = analyse_trend(populated_store, limit=20)
        assert summary.consecutive_failures == 2

    def test_last_status_reflects_most_recent(self, populated_store: HistoryStore):
        summary = analyse_trend(populated_store, limit=20)
        assert summary.last_status == "FAIL"

    def test_limit_respected(self, populated_store: HistoryStore):
        summary = analyse_trend(populated_store, limit=2)
        assert summary.total_runs == 2
