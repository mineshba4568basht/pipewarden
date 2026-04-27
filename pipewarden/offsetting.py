"""Offset tracking for pipeline metrics.

Allows recording and comparing metric offsets over time so that
relative changes (deltas) can be monitored independently of absolute
values.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class OffsetEntry:
    pipeline: str
    metric: str
    value: float
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __str__(self) -> str:
        ts = self.recorded_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        return f"[{ts}] {self.pipeline}/{self.metric} offset={self.value:.4f}"


@dataclass
class OffsetDelta:
    pipeline: str
    metric: str
    previous: float
    current: float

    @property
    def delta(self) -> float:
        return self.current - self.previous

    @property
    def pct_change(self) -> Optional[float]:
        if self.previous == 0.0:
            return None
        return (self.delta / abs(self.previous)) * 100.0

    def __str__(self) -> str:
        pct = f"{self.pct_change:.2f}%" if self.pct_change is not None else "n/a"
        return (
            f"{self.pipeline}/{self.metric} "
            f"prev={self.previous:.4f} cur={self.current:.4f} "
            f"delta={self.delta:+.4f} ({pct})"
        )


class OffsetStore:
    """In-memory store for offset entries."""

    def __init__(self) -> None:
        self._entries: List[OffsetEntry] = []

    def record(self, pipeline: str, metric: str, value: float) -> OffsetEntry:
        entry = OffsetEntry(pipeline=pipeline, metric=metric, value=value)
        self._entries.append(entry)
        return entry

    def latest(self, pipeline: str, metric: str) -> Optional[OffsetEntry]:
        matches = [
            e for e in self._entries
            if e.pipeline == pipeline and e.metric == metric
        ]
        return matches[-1] if matches else None

    def diff(self, pipeline: str, metric: str, new_value: float) -> Optional[OffsetDelta]:
        prev = self.latest(pipeline, metric)
        if prev is None:
            return None
        return OffsetDelta(
            pipeline=pipeline,
            metric=metric,
            previous=prev.value,
            current=new_value,
        )

    def list_entries(
        self, pipeline: Optional[str] = None, limit: int = 50
    ) -> List[OffsetEntry]:
        entries = [
            e for e in self._entries
            if pipeline is None or e.pipeline == pipeline
        ]
        return entries[-limit:]

    def clear(self) -> int:
        count = len(self._entries)
        self._entries.clear()
        return count
