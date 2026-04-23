"""Sliding and tumbling window aggregation for alert event streams."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from pipewarden.runner import AlertEvent


@dataclass
class WindowPolicy:
    """Configuration for a time-based event window."""

    size_seconds: int = 300  # 5 minutes
    slide_seconds: Optional[int] = None  # None => tumbling window

    def __post_init__(self) -> None:
        if self.size_seconds <= 0:
            raise ValueError("size_seconds must be positive")
        if self.slide_seconds is not None and self.slide_seconds <= 0:
            raise ValueError("slide_seconds must be positive")
        if self.slide_seconds is not None and self.slide_seconds > self.size_seconds:
            raise ValueError("slide_seconds cannot exceed size_seconds")

    @property
    def is_sliding(self) -> bool:
        return self.slide_seconds is not None

    def __str__(self) -> str:
        kind = "sliding" if self.is_sliding else "tumbling"
        return f"WindowPolicy({kind}, size={self.size_seconds}s)"


@dataclass
class WindowBucket:
    """A single window bucket containing aggregated events."""

    start: datetime
    end: datetime
    events: List[AlertEvent] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.events)

    @property
    def failure_count(self) -> int:
        return sum(1 for e in self.events if not e.rule.severity == "info")

    @property
    def pipelines(self) -> List[str]:
        return list({e.pipeline for e in self.events})

    def __str__(self) -> str:
        return (
            f"WindowBucket({self.start.isoformat()} -> {self.end.isoformat()}, "
            f"events={self.count})"
        )


def build_windows(
    events: List[AlertEvent],
    policy: WindowPolicy,
    reference: Optional[datetime] = None,
) -> List[WindowBucket]:
    """Partition *events* into window buckets according to *policy*.

    Events are matched by their ``triggered_at`` timestamp.  For tumbling
    windows the step equals the window size; for sliding windows the step
    equals ``slide_seconds``.
    """
    if not events:
        return []

    ref = reference or datetime.utcnow()
    size = timedelta(seconds=policy.size_seconds)
    step = timedelta(seconds=policy.slide_seconds or policy.size_seconds)

    # Determine the earliest event timestamp to anchor the first bucket.
    earliest = min(e.triggered_at for e in events)
    buckets: List[WindowBucket] = []
    start = earliest
    while start < ref:
        end = start + size
        bucket = WindowBucket(start=start, end=end)
        for evt in events:
            if start <= evt.triggered_at < end:
                bucket.events.append(evt)
        buckets.append(bucket)
        start += step

    return buckets
