"""Daily/periodic digest report generation for pipeline health summaries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from pipewarden.history import HistoryStore, HistoryEntry
from pipewarden.trend import analyse_trend, TrendSummary


@dataclass
class DigestEntry:
    pipeline: str
    total_runs: int
    passed_runs: int
    failed_runs: int
    trend: TrendSummary
    last_run_at: Optional[datetime] = None

    @property
    def pass_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.passed_runs / self.total_runs

    def __str__(self) -> str:
        status = "OK" if self.trend.consecutive_failures == 0 else "DEGRADED"
        return (
            f"[{status}] {self.pipeline}: "
            f"{self.passed_runs}/{self.total_runs} passed "
            f"({self.pass_rate:.0%}), "
            f"streak_failures={self.trend.consecutive_failures}"
        )


@dataclass
class DigestReport:
    generated_at: datetime = field(default_factory=datetime.utcnow)
    period_hours: int = 24
    entries: List[DigestEntry] = field(default_factory=list)

    @property
    def healthy_pipelines(self) -> List[DigestEntry]:
        return [e for e in self.entries if e.trend.consecutive_failures == 0]

    @property
    def degraded_pipelines(self) -> List[DigestEntry]:
        return [e for e in self.entries if e.trend.consecutive_failures > 0]

    def __str__(self) -> str:
        lines = [
            f"=== PipeWarden Digest ({self.period_hours}h) — {self.generated_at.strftime('%Y-%m-%d %H:%M')} UTC ===",
            f"Pipelines: {len(self.entries)} total, "
            f"{len(self.healthy_pipelines)} healthy, "
            f"{len(self.degraded_pipelines)} degraded",
            "",
        ]
        for entry in self.entries:
            lines.append(f"  {entry}")
        return "\n".join(lines)


def build_digest(store: HistoryStore, period_hours: int = 24) -> DigestReport:
    """Build a digest report from history entries within the given period."""
    cutoff = datetime.utcnow() - timedelta(hours=period_hours)
    all_entries: List[HistoryEntry] = [
        e for e in store.load() if e.run_at >= cutoff
    ]

    pipelines: dict[str, List[HistoryEntry]] = {}
    for entry in all_entries:
        pipelines.setdefault(entry.pipeline, []).append(entry)

    digest_entries: List[DigestEntry] = []
    for pipeline, entries in sorted(pipelines.items()):
        trend = analyse_trend(store, pipeline=pipeline, limit=len(entries))
        passed = sum(1 for e in entries if e.passed)
        last = max(entries, key=lambda e: e.run_at, default=None)
        digest_entries.append(
            DigestEntry(
                pipeline=pipeline,
                total_runs=len(entries),
                passed_runs=passed,
                failed_runs=len(entries) - passed,
                trend=trend,
                last_run_at=last.run_at if last else None,
            )
        )

    return DigestReport(
        period_hours=period_hours,
        entries=digest_entries,
    )
