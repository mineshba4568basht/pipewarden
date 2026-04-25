"""Watermark tracking for pipeline event-time progress."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class WatermarkEntry:
    pipeline: str
    event_time: datetime
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    lag_seconds: float = 0.0

    def __str__(self) -> str:  # pragma: no cover
        lag = f"{self.lag_seconds:.1f}s lag"
        return f"[{self.pipeline}] event_time={self.event_time.isoformat()} ({lag})"


@dataclass
class WatermarkLagResult:
    pipeline: str
    current_watermark: datetime
    wall_clock: datetime
    lag_seconds: float
    threshold_seconds: float
    breached: bool

    def __str__(self) -> str:  # pragma: no cover
        status = "BREACHED" if self.breached else "OK"
        return (
            f"[{self.pipeline}] watermark lag {self.lag_seconds:.1f}s "
            f"(threshold {self.threshold_seconds:.1f}s) [{status}]"
        )


class WatermarkStore:
    """In-memory store for per-pipeline watermarks."""

    def __init__(self) -> None:
        self._marks: Dict[str, WatermarkEntry] = {}

    def update(self, pipeline: str, event_time: datetime) -> WatermarkEntry:
        """Advance the watermark for *pipeline* if *event_time* is newer."""
        existing = self._marks.get(pipeline)
        wall = datetime.now(timezone.utc)
        # Ensure event_time is tz-aware for comparison
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        if existing is None or event_time > existing.event_time:
            lag = max(0.0, (wall - event_time).total_seconds())
            entry = WatermarkEntry(
                pipeline=pipeline,
                event_time=event_time,
                recorded_at=wall,
                lag_seconds=lag,
            )
            self._marks[pipeline] = entry
            return entry
        return existing

    def get(self, pipeline: str) -> Optional[WatermarkEntry]:
        return self._marks.get(pipeline)

    def all(self) -> List[WatermarkEntry]:
        return list(self._marks.values())

    def clear(self, pipeline: Optional[str] = None) -> int:
        if pipeline:
            removed = int(pipeline in self._marks)
            self._marks.pop(pipeline, None)
            return removed
        count = len(self._marks)
        self._marks.clear()
        return count


def check_lag(
    store: WatermarkStore,
    pipeline: str,
    threshold_seconds: float = 300.0,
    wall_clock: Optional[datetime] = None,
) -> WatermarkLagResult:
    """Return a lag result for *pipeline* against *threshold_seconds*."""
    entry = store.get(pipeline)
    wall = wall_clock or datetime.now(timezone.utc)
    if entry is None:
        return WatermarkLagResult(
            pipeline=pipeline,
            current_watermark=wall,
            wall_clock=wall,
            lag_seconds=0.0,
            threshold_seconds=threshold_seconds,
            breached=False,
        )
    lag = max(0.0, (wall - entry.event_time).total_seconds())
    return WatermarkLagResult(
        pipeline=pipeline,
        current_watermark=entry.event_time,
        wall_clock=wall,
        lag_seconds=lag,
        threshold_seconds=threshold_seconds,
        breached=lag > threshold_seconds,
    )
