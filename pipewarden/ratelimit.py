"""Rate limiting for alert dispatching — caps alerts per pipeline per window."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List

from pipewarden.runner import AlertEvent


@dataclass
class RateLimitPolicy:
    max_alerts: int = 5
    window_seconds: int = 300

    def __post_init__(self) -> None:
        if self.max_alerts < 1:
            raise ValueError("max_alerts must be >= 1")
        if self.window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")

    def __str__(self) -> str:
        return f"RateLimitPolicy(max={self.max_alerts}, window={self.window_seconds}s)"


@dataclass
class RateLimitResult:
    event: AlertEvent
    allowed: bool
    current_count: int
    limit: int

    def __str__(self) -> str:
        status = "ALLOWED" if self.allowed else "BLOCKED"
        return (
            f"[{status}] {self.event.rule.name} on {self.event.pipeline} "
            f"({self.current_count}/{self.limit})"
        )


class RateLimiter:
    """Tracks alert counts per pipeline within a sliding window."""

    def __init__(self, policy: RateLimitPolicy | None = None) -> None:
        self.policy = policy or RateLimitPolicy()
        self._timestamps: Dict[str, List[datetime]] = {}

    def check(self, event: AlertEvent, now: datetime | None = None) -> RateLimitResult:
        now = now or datetime.utcnow()
        key = event.pipeline
        cutoff = now - timedelta(seconds=self.policy.window_seconds)
        bucket = [t for t in self._timestamps.get(key, []) if t >= cutoff]
        self._timestamps[key] = bucket
        allowed = len(bucket) < self.policy.max_alerts
        if allowed:
            self._timestamps[key].append(now)
        return RateLimitResult(
            event=event,
            allowed=allowed,
            current_count=len(self._timestamps[key]),
            limit=self.policy.max_alerts,
        )

    def reset(self, pipeline: str) -> None:
        self._timestamps.pop(pipeline, None)

    def reset_all(self) -> None:
        self._timestamps.clear()
