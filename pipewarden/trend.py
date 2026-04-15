"""Trend analysis over pipeline run history."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewarden.history import HistoryEntry, HistoryStore


@dataclass
class TrendSummary:
    """Aggregated trend statistics for a pipeline."""

    total_runs: int
    passed_runs: int
    failed_runs: int
    pass_rate: float  # 0.0 – 1.0
    consecutive_failures: int
    last_status: Optional[str] = None

    def __str__(self) -> str:
        status = self.last_status or "unknown"
        return (
            f"TrendSummary(runs={self.total_runs}, "
            f"pass_rate={self.pass_rate:.0%}, "
            f"consecutive_failures={self.consecutive_failures}, "
            f"last={status})"
        )


def _consecutive_failures(entries: List[HistoryEntry]) -> int:
    """Count failures from the most recent entry backwards."""
    count = 0
    for entry in reversed(entries):
        if entry.status == "FAIL":
            count += 1
        else:
            break
    return count


def analyse_trend(store: HistoryStore, limit: int = 20) -> TrendSummary:
    """Return a TrendSummary built from the most recent *limit* history entries."""
    entries: List[HistoryEntry] = store.list(limit=limit)

    if not entries:
        return TrendSummary(
            total_runs=0,
            passed_runs=0,
            failed_runs=0,
            pass_rate=0.0,
            consecutive_failures=0,
            last_status=None,
        )

    passed = sum(1 for e in entries if e.status == "PASS")
    failed = len(entries) - passed
    pass_rate = passed / len(entries)
    consec = _consecutive_failures(entries)
    last_status = entries[-1].status

    return TrendSummary(
        total_runs=len(entries),
        passed_runs=passed,
        failed_runs=failed,
        pass_rate=pass_rate,
        consecutive_failures=consec,
        last_status=last_status,
    )
