"""Audit log for pipeline check events."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    pipeline: str
    check: str
    status: str  # "pass" | "fail"
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __str__(self) -> str:
        ts = self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        return f"[{ts}] {self.pipeline}/{self.check} -> {self.status}: {self.message}"

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "check": self.check,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            pipeline=data["pipeline"],
            check=data["check"],
            status=data["status"],
            message=data["message"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class AuditLog:
    def __init__(self, path: str = ".pipewarden_audit.json") -> None:
        self._path = Path(path)
        self._entries: List[AuditEntry] = self._load()

    def _load(self) -> List[AuditEntry]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text())
            return [AuditEntry.from_dict(r) for r in raw]
        except (json.JSONDecodeError, KeyError):
            return []

    def _save(self) -> None:
        self._path.write_text(json.dumps([e.to_dict() for e in self._entries], indent=2))

    def record(self, entry: AuditEntry) -> None:
        self._entries.append(entry)
        self._save()

    def entries(
        self,
        pipeline: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditEntry]:
        result = self._entries
        if pipeline:
            result = [e for e in result if e.pipeline == pipeline]
        return result[-limit:]

    def clear(self) -> int:
        count = len(self._entries)
        self._entries = []
        self._save()
        return count
