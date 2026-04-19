"""Alert quota enforcement — cap total alerts per pipeline per time window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List

from pipewarden.runner import AlertEvent


@dataclass
class QuotaPolicy:
    max_alerts: int = 10
    window_minutes: int = 60

    def __post_init__(self) -> None:
        if self.max_alerts < 1:
            raise ValueError("max_alerts must be >= 1")
        if self.window_minutes < 1:
            raise ValueError("window_minutes must be >= 1")

    def __str__(self) -> str:
        return f"QuotaPolicy(max={self.max_alerts}, window={self.window_minutes}m)"


@dataclass
class QuotaResult:
    event: AlertEvent
    allowed: bool
    current_count: int
    limit: int

    def __str__(self) -> str:
        status = "allowed" if self.allowed else "blocked"
        return (
            f"QuotaResult({status} | {self.event.rule.name} | "
            f"{self.current_count}/{self.limit})"
        )


@dataclass
class QuotaManager:
    policy: QuotaPolicy = field(default_factory=QuotaPolicy)
    _log: Dict[str, List[datetime]] = field(default_factory=dict, repr=False)

    def check(self, event: AlertEvent, now: datetime | None = None) -> QuotaResult:
        now = now or datetime.utcnow()
        key = event.pipeline
        cutoff = now - timedelta(minutes=self.policy.window_minutes)
        entries = [t for t in self._log.get(key, []) if t >= cutoff]
        self._log[key] = entries
        allowed = len(entries) < self.policy.max_alerts
        if allowed:
            self._log[key].append(now)
        return QuotaResult(
            event=event,
            allowed=allowed,
            current_count=len(self._log[key]),
            limit=self.policy.max_alerts,
        )

    def reset(self, pipeline: str) -> None:
        self._log.pop(pipeline, None)

    def usage(self, pipeline: str, now: datetime | None = None) -> int:
        now = now or datetime.utcnow()
        cutoff = now - timedelta(minutes=self.policy.window_minutes)
        return sum(1 for t in self._log.get(pipeline, []) if t >= cutoff)
