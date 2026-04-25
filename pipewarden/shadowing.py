"""Shadow mode: run checks without triggering real alerts, for safe testing."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from pipewarden.runner import AlertEvent


@dataclass
class ShadowRecord:
    pipeline: str
    check: str
    would_alert: bool
    severity: str
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __str__(self) -> str:
        status = "WOULD ALERT" if self.would_alert else "silent"
        ts = self.recorded_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        return f"[{ts}] shadow {self.pipeline}/{self.check} -> {status} (severity={self.severity})"


@dataclass
class ShadowPolicy:
    enabled: bool = True
    log_silent: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool")

    def __str__(self) -> str:
        return f"ShadowPolicy(enabled={self.enabled}, log_silent={self.log_silent})"


class ShadowManager:
    """Intercepts AlertEvents in shadow mode and records what would have fired."""

    def __init__(self, policy: Optional[ShadowPolicy] = None) -> None:
        self._policy = policy or ShadowPolicy()
        self._records: List[ShadowRecord] = []

    @property
    def policy(self) -> ShadowPolicy:
        return self._policy

    def evaluate(self, event: AlertEvent) -> ShadowRecord:
        """Record a shadow evaluation for *event* without dispatching it."""
        would_alert = not event.rule.enabled if hasattr(event.rule, "enabled") else True
        # Treat every event passed to shadow mode as "would alert"
        would_alert = True
        rec = ShadowRecord(
            pipeline=event.pipeline,
            check=event.check_name,
            would_alert=would_alert,
            severity=event.rule.severity,
        )
        if would_alert or self._policy.log_silent:
            self._records.append(rec)
        return rec

    def records(self, pipeline: Optional[str] = None) -> List[ShadowRecord]:
        if pipeline is None:
            return list(self._records)
        return [r for r in self._records if r.pipeline == pipeline]

    def clear(self) -> int:
        n = len(self._records)
        self._records.clear()
        return n

    def summary(self) -> str:
        total = len(self._records)
        alerts = sum(1 for r in self._records if r.would_alert)
        return f"ShadowManager: {total} evaluated, {alerts} would-alert"
