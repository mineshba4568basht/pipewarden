"""Alert event aggregation — group and reduce events over a time window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from pipewarden.runner import AlertEvent


@dataclass
class AggregationPolicy:
    """Rules that control how events are aggregated."""

    window_seconds: int = 60
    max_events: int = 100
    group_by: str = "pipeline"  # "pipeline", "check", or "severity"

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if self.max_events <= 0:
            raise ValueError("max_events must be positive")
        if self.group_by not in ("pipeline", "check", "severity"):
            raise ValueError("group_by must be 'pipeline', 'check', or 'severity'")

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"AggregationPolicy(window={self.window_seconds}s, "
            f"max={self.max_events}, group_by={self.group_by})"
        )


@dataclass
class AggregatedBucket:
    """A bucket of events sharing the same group key."""

    key: str
    events: List[AlertEvent] = field(default_factory=list)
    opened_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def count(self) -> int:
        return len(self.events)

    @property
    def severities(self) -> List[str]:
        return [e.rule.severity for e in self.events]

    def __str__(self) -> str:
        return f"AggregatedBucket(key={self.key!r}, count={self.count})"


def _group_key(event: AlertEvent, group_by: str) -> str:
    if group_by == "check":
        return event.check_result.rule.name
    if group_by == "severity":
        return event.rule.severity
    return event.pipeline


def aggregate(
    events: List[AlertEvent],
    policy: AggregationPolicy,
    now: Optional[datetime] = None,
) -> List[AggregatedBucket]:
    """Aggregate *events* into buckets according to *policy*."""
    cutoff = (now or datetime.utcnow()) - timedelta(seconds=policy.window_seconds)
    recent = [e for e in events if e.triggered_at >= cutoff][: policy.max_events]

    buckets: dict[str, AggregatedBucket] = {}
    for event in recent:
        key = _group_key(event, policy.group_by)
        if key not in buckets:
            buckets[key] = AggregatedBucket(key=key)
        buckets[key].events.append(event)

    return list(buckets.values())
