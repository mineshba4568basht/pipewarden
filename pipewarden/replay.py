"""Replay historical pipeline runs for debugging and validation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from pipewarden.history import HistoryEntry, HistoryStore
from pipewarden.runner import RunReport


@dataclass
class ReplayResult:
    """Outcome of replaying a slice of history."""

    entries: List[HistoryEntry]
    pipeline: str
    start: datetime
    end: datetime
    total: int = field(init=False)
    failures: int = field(init=False)

    def __post_init__(self) -> None:
        self.total = len(self.entries)
        self.failures = sum(1 for e in self.entries if not e.passed)

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.total - self.failures) / self.total

    def __str__(self) -> str:
        pct = f"{self.pass_rate * 100:.1f}%"
        return (
            f"ReplayResult(pipeline={self.pipeline!r}, "
            f"total={self.total}, failures={self.failures}, pass_rate={pct})"
        )


def replay(
    store: HistoryStore,
    pipeline: str,
    start: datetime,
    end: datetime,
    limit: Optional[int] = None,
) -> ReplayResult:
    """Return history entries for *pipeline* between *start* and *end*."""
    raw = store.list(pipeline=pipeline, limit=limit or 1000)
    filtered = [
        e for e in raw
        if start <= e.recorded_at <= end
    ]
    return ReplayResult(
        entries=filtered,
        pipeline=pipeline,
        start=start,
        end=end,
    )
