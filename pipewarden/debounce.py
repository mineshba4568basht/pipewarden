"""Debounce alerts: only fire after N consecutive failures."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from pipewarden.runner import AlertEvent


@dataclass
class DebounceRecord:
    pipeline: str
    check: str
    consecutive_failures: int = 0
    last_seen: Optional[datetime] = None

    def __str__(self) -> str:
        return (
            f"DebounceRecord({self.pipeline}/{self.check} "
            f"failures={self.consecutive_failures})"
        )


@dataclass
class DebouncePolicy:
    threshold: int = 2

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise ValueError("threshold must be >= 1")

    def __str__(self) -> str:
        return f"DebouncePolicy(threshold={self.threshold})"


@dataclass
class DebounceManager:
    policy: DebouncePolicy = field(default_factory=DebouncePolicy)
    _records: Dict[str, DebounceRecord] = field(default_factory=dict, init=False)

    def _key(self, event: AlertEvent) -> str:
        return f"{event.rule.pipeline}::{event.result.check_name}"

    def should_fire(self, event: AlertEvent) -> bool:
        """Return True when the failure count reaches the threshold."""
        key = self._key(event)
        if event.result.passed:
            self._records.pop(key, None)
            return False
        rec = self._records.get(key)
        if rec is None:
            rec = DebounceRecord(
                pipeline=event.rule.pipeline,
                check=event.result.check_name,
            )
            self._records[key] = rec
        rec.consecutive_failures += 1
        rec.last_seen = datetime.utcnow()
        return rec.consecutive_failures >= self.policy.threshold

    def reset(self, pipeline: str, check: str) -> None:
        key = f"{pipeline}::{check}"
        self._records.pop(key, None)

    def record_for(self, pipeline: str, check: str) -> Optional[DebounceRecord]:
        return self._records.get(f"{pipeline}::{check}")
