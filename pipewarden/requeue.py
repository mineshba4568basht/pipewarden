"""Requeue module: track and manage failed checks eligible for retry."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from pipewarden.runner import AlertEvent


@dataclass
class RequeueEntry:
    pipeline: str
    check_name: str
    severity: str
    reason: str
    attempts: int = 0
    queued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_attempted_at: Optional[datetime] = None

    def __str__(self) -> str:
        ts = self.queued_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        return (
            f"[REQUEUE] {self.pipeline}/{self.check_name} "
            f"severity={self.severity} attempts={self.attempts} queued={ts}"
        )

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "check_name": self.check_name,
            "severity": self.severity,
            "reason": self.reason,
            "attempts": self.attempts,
            "queued_at": self.queued_at.isoformat(),
            "last_attempted_at": (
                self.last_attempted_at.isoformat() if self.last_attempted_at else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RequeueEntry":
        last = data.get("last_attempted_at")
        return cls(
            pipeline=data["pipeline"],
            check_name=data["check_name"],
            severity=data["severity"],
            reason=data["reason"],
            attempts=data.get("attempts", 0),
            queued_at=datetime.fromisoformat(data["queued_at"]),
            last_attempted_at=datetime.fromisoformat(last) if last else None,
        )


class RequeueStore:
    def __init__(self, path: str = ".pipewarden_requeue.json") -> None:
        self._path = Path(path)
        self._entries: List[RequeueEntry] = self._load()

    def _load(self) -> List[RequeueEntry]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text())
            return [RequeueEntry.from_dict(r) for r in raw]
        except (json.JSONDecodeError, KeyError):
            return []

    def _save(self) -> None:
        self._path.write_text(json.dumps([e.to_dict() for e in self._entries], indent=2))

    def enqueue(self, event: AlertEvent) -> RequeueEntry:
        entry = RequeueEntry(
            pipeline=event.rule.pipeline,
            check_name=event.result.check_name,
            severity=event.rule.severity,
            reason=str(event.result),
        )
        self._entries.append(entry)
        self._save()
        return entry

    def mark_attempted(self, entry: RequeueEntry) -> None:
        entry.attempts += 1
        entry.last_attempted_at = datetime.now(timezone.utc)
        self._save()

    def remove(self, entry: RequeueEntry) -> None:
        self._entries = [e for e in self._entries if e is not entry]
        self._save()

    def pending(self, max_attempts: int = 3) -> List[RequeueEntry]:
        return [e for e in self._entries if e.attempts < max_attempts]

    def all(self) -> List[RequeueEntry]:
        return list(self._entries)

    def clear(self) -> int:
        count = len(self._entries)
        self._entries = []
        self._save()
        return count
