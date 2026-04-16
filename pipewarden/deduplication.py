"""Alert deduplication – suppress repeated alerts within a cooldown window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from pipewarden.runner import AlertEvent


@dataclass
class DedupeRecord:
    pipeline: str
    check_name: str
    first_seen: datetime
    last_seen: datetime
    count: int = 1

    def __str__(self) -> str:
        return (
            f"DedupeRecord({self.pipeline}/{self.check_name} "
            f"x{self.count} last={self.last_seen.isoformat()})"
        )


@dataclass
class DeduplicationFilter:
    """Suppress duplicate AlertEvents fired within *cooldown_minutes*."""

    cooldown_minutes: int = 30
    _records: Dict[str, DedupeRecord] = field(default_factory=dict, init=False, repr=False)

    def _key(self, event: AlertEvent) -> str:
        return f"{event.pipeline}::{event.rule.check_name}"

    def is_duplicate(self, event: AlertEvent, now: Optional[datetime] = None) -> bool:
        """Return True if *event* should be suppressed."""
        now = now or datetime.utcnow()
        key = self._key(event)
        record = self._records.get(key)
        if record is None:
            return False
        cutoff = record.last_seen + timedelta(minutes=self.cooldown_minutes)
        return now < cutoff

    def register(self, event: AlertEvent, now: Optional[datetime] = None) -> DedupeRecord:
        """Record that *event* fired; return the DedupeRecord."""
        now = now or datetime.utcnow()
        key = self._key(event)
        record = self._records.get(key)
        if record is None:
            record = DedupeRecord(
                pipeline=event.pipeline,
                check_name=event.rule.check_name,
                first_seen=now,
                last_seen=now,
            )
            self._records[key] = record
        else:
            record.last_seen = now
            record.count += 1
        return record

    def clear(self, pipeline: Optional[str] = None) -> int:
        """Remove records, optionally scoped to *pipeline*. Returns count removed."""
        if pipeline is None:
            removed = len(self._records)
            self._records.clear()
            return removed
        keys = [k for k in self._records if k.startswith(f"{pipeline}::")]
        for k in keys:
            del self._records[k]
        return len(keys)
