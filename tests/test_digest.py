"""Tests for pipewarden.digest module."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from pipewarden.digest import DigestEntry, DigestReport, build_digest
from pipewarden.history import HistoryStore, HistoryEntry
from pipewarden.trend import TrendSummary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trend(consecutive_failures: int = 0) -> TrendSummary:
    return TrendSummary(
        pipeline="pipe",
        total=5,
        passed=5 - consecutive_failures,
        failed=consecutive_failures,
        consecutive_failures=consecutive_failures,
        pass_rate=1.0 - consecutive_failures / 5,
    )


@pytest.fixture()
def store(tmp_path: Path) -> HistoryStore:
    now = datetime.utcnow()
    entries = [
        HistoryEntry(pipeline="alpha", passed=True, run_at=now - timedelta(hours=1), check_count=3, failed_checks=0),
        HistoryEntry(pipeline="alpha", passed=False, run_at=now - timedelta(hours=2), check_count=3, failed_checks=1),
        HistoryEntry(pipeline="beta", passed=True, run_at=now - timedelta(hours=3), check_count=2, failed_checks=0),
    ]
    history_file = tmp_path / "history.json"
    history_file.write_text(
        json.dumps([e.__dict__ | {"run_at": e.run_at.isoformat()} for e in entries])
    )
    return HistoryStore(path=str(history_file))


# ---------------------------------------------------------------------------
# DigestEntry
# ---------------------------------------------------------------------------

class TestDigestEntry:
    def test_pass_rate_full(self):
        entry = DigestEntry("pipe", total_runs=4, passed_runs=4, failed_runs=0, trend=_make_trend(0))
        assert entry.pass_rate == 1.0

    def test_pass_rate_partial(self):
        entry = DigestEntry("pipe", total_runs=4, passed_runs=3, failed_runs=1, trend=_make_trend(0))
        assert entry.pass_rate == pytest.approx(0.75)

    def test_pass_rate_zero_runs(self):
        entry = DigestEntry("pipe", total_runs=0, passed_runs=0, failed_runs=0, trend=_make_trend(0))
        assert entry.pass_rate == 0.0

    def test_str_ok_status(self):
        entry = DigestEntry("pipe", total_runs=2, passed_runs=2, failed_runs=0, trend=_make_trend(0))
        assert "[OK]" in str(entry)
        assert "pipe" in str(entry)

    def test_str_degraded_status(self):
        entry = DigestEntry("pipe", total_runs=2, passed_runs=1, failed_runs=1, trend=_make_trend(1))
        assert "[DEGRADED]" in str(entry)


# ---------------------------------------------------------------------------
# DigestReport
# ---------------------------------------------------------------------------

class TestDigestReport:
    def test_healthy_pipelines_filter(self):
        entries = [
            DigestEntry("ok", 1, 1, 0, _make_trend(0)),
            DigestEntry("bad", 1, 0, 1, _make_trend(1)),
        ]
        report = DigestReport(entries=entries)
        assert len(report.healthy_pipelines) == 1
        assert report.healthy_pipelines[0].pipeline == "ok"

    def test_degraded_pipelines_filter(self):
        entries = [
            DigestEntry("ok", 1, 1, 0, _make_trend(0)),
            DigestEntry("bad", 1, 0, 1, _make_trend(2)),
        ]
        report = DigestReport(entries=entries)
        assert len(report.degraded_pipelines) == 1

    def test_str_contains_header(self):
        report = DigestReport(entries=[])
        assert "PipeWarden Digest" in str(report)

    def test_str_shows_counts(self):
        entries = [
            DigestEntry("ok", 1, 1, 0, _make_trend(0)),
            DigestEntry("bad", 1, 0, 1, _make_trend(1)),
        ]
        report = DigestReport(entries=entries)
        result = str(report)
        assert "2 total" in result
        assert "1 healthy" in result
        assert "1 degraded" in result


# ---------------------------------------------------------------------------
# build_digest
# ---------------------------------------------------------------------------

class TestBuildDigest:
    def test_returns_digest_report(self, store: HistoryStore):
        report = build_digest(store, period_hours=24)
        assert isinstance(report, DigestReport)

    def test_pipelines_discovered(self, store: HistoryStore):
        report = build_digest(store, period_hours=24)
        names = {e.pipeline for e in report.entries}
        assert "alpha" in names
        assert "beta" in names

    def test_run_counts_correct(self, store: HistoryStore):
        report = build_digest(store, period_hours=24)
        alpha = next(e for e in report.entries if e.pipeline == "alpha")
        assert alpha.total_runs == 2
        assert alpha.passed_runs == 1
        assert alpha.failed_runs == 1

    def test_empty_store_returns_no_entries(self, tmp_path: Path):
        empty = HistoryStore(path=str(tmp_path / "empty.json"))
        report = build_digest(empty, period_hours=24)
        assert report.entries == []

    def test_period_filters_old_entries(self, store: HistoryStore):
        # period of 0 hours means nothing is in range
        report = build_digest(store, period_hours=0)
        assert report.entries == []
