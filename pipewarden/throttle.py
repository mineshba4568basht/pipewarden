"""Alert throttling to suppress repeated alerts within a cooldown window."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class ThrottleRecord:
    pipeline: str
    check: str
    first_fired: datetime
    last_fired: datetime
    suppressed_count: int = 0

    def __str__(self) -> str:
        return (
            f"ThrottleRecord({self.pipeline}/{self.check} "
            f"first={self.first_fired.isoformat()} "
            f"suppressed={self.suppressed_count})"
        )


@dataclass
class ThrottlePolicy:
    cooldown_minutes: int = 30
    max_suppressed: Optional[int] = None  # None = unlimited

    def __post_init__(self) -> None:
        if self.cooldown_minutes < 1:
            raise ValueError("cooldown_minutes must be >= 1")


@dataclass
class ThrottleManager:
    policy: ThrottlePolicy = field(default_factory=ThrottlePolicy)
    _records: Dict[str, ThrottleRecord] = field(default_factory=dict, init=False)

    def _key(self, pipeline: str, check: str) -> str:
        return f"{pipeline}::{check}"

    def is_throttled(self, pipeline: str, check: str, now: Optional[datetime] = None) -> bool:
        """Return True if the alert should be suppressed."""
        now = now or datetime.utcnow()
        key = self._key(pipeline, check)
        rec = self._records.get(key)
        if rec is None:
            return False
        cooldown = timedelta(minutes=self.policy.cooldown_minutes)
        if now - rec.last_fired < cooldown:
            if self.policy.max_suppressed is None or rec.suppressed_count < self.policy.max_suppressed:
                return True
        return False

    def record(self, pipeline: str, check: str, now: Optional[datetime] = None) -> ThrottleRecord:
        """Record a fired alert; returns the updated record."""
        now = now or datetime.utcnow()
        key = self._key(pipeline, check)
        rec = self._records.get(key)
        if rec is None:
            rec = ThrottleRecord(pipeline=pipeline, check=check, first_fired=now, last_fired=now)
            self._records[key] = rec
        else:
            cooldown = timedelta(minutes=self.policy.cooldown_minutes)
            if now - rec.last_fired < cooldown:
                rec.suppressed_count += 1
            else:
                rec.suppressed_count = 0
                rec.first_fired = now
            rec.last_fired = now
        return rec

    def clear(self, pipeline: str, check: str) -> None:
        self._records.pop(self._key(pipeline, check), None)

    def active_records(self) -> list[ThrottleRecord]:
        return list(self._records.values())
