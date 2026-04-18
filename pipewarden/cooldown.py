"""Cooldown tracking: suppress repeated alerts for the same pipeline/check."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class CooldownEntry:
    pipeline: str
    check: str
    last_alert: datetime
    cooldown_seconds: int

    def is_cooling(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        return (now - self.last_alert).total_seconds() < self.cooldown_seconds

    def expires_at(self) -> datetime:
        return self.last_alert + timedelta(seconds=self.cooldown_seconds)

    def __str__(self) -> str:
        status = "cooling" if self.is_cooling() else "ready"
        return (
            f"CooldownEntry({self.pipeline}/{self.check} "
            f"last={self.last_alert.isoformat()} status={status})"
        )


class CooldownManager:
    def __init__(self, default_cooldown: int = 300) -> None:
        if default_cooldown < 0:
            raise ValueError("default_cooldown must be >= 0")
        self.default_cooldown = default_cooldown
        self._entries: Dict[str, CooldownEntry] = {}

    def _key(self, pipeline: str, check: str) -> str:
        return f"{pipeline}::{check}"

    def is_cooling(self, pipeline: str, check: str, now: Optional[datetime] = None) -> bool:
        key = self._key(pipeline, check)
        entry = self._entries.get(key)
        if entry is None:
            return False
        return entry.is_cooling(now)

    def record(self, pipeline: str, check: str, now: Optional[datetime] = None) -> CooldownEntry:
        now = now or datetime.utcnow()
        key = self._key(pipeline, check)
        entry = CooldownEntry(
            pipeline=pipeline,
            check=check,
            last_alert=now,
            cooldown_seconds=self.default_cooldown,
        )
        self._entries[key] = entry
        return entry

    def clear(self, pipeline: str, check: str) -> bool:
        key = self._key(pipeline, check)
        if key in self._entries:
            del self._entries[key]
            return True
        return False

    def all_entries(self) -> list:
        return list(self._entries.values())
