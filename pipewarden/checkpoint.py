"""Checkpoint tracking — record and compare pipeline run states."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json, pathlib


@dataclass
class CheckpointEntry:
    pipeline: str
    check_name: str
    status: str  # "pass" | "fail"
    value: float
    recorded_at: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        ts = self.recorded_at.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{ts}] {self.pipeline}/{self.check_name} {self.status} value={self.value}"

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "check_name": self.check_name,
            "status": self.status,
            "value": self.value,
            "recorded_at": self.recorded_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CheckpointEntry":
        return cls(
            pipeline=d["pipeline"],
            check_name=d["check_name"],
            status=d["status"],
            value=float(d["value"]),
            recorded_at=datetime.fromisoformat(d["recorded_at"]),
        )


class CheckpointStore:
    def __init__(self, path: str = ".pipewarden_checkpoints.json") -> None:
        self._path = pathlib.Path(path)
        self._entries: list[CheckpointEntry] = self._load()

    def _load(self) -> list[CheckpointEntry]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text())
            return [CheckpointEntry.from_dict(r) for r in raw]
        except Exception:
            return []

    def _save(self) -> None:
        self._path.write_text(json.dumps([e.to_dict() for e in self._entries], indent=2))

    def record(self, entry: CheckpointEntry) -> None:
        self._entries.append(entry)
        self._save()

    def latest(self, pipeline: str, check_name: str) -> Optional[CheckpointEntry]:
        matches = [e for e in self._entries if e.pipeline == pipeline and e.check_name == check_name]
        return matches[-1] if matches else None

    def all_entries(self, limit: int = 50) -> list[CheckpointEntry]:
        return self._entries[-limit:]

    def clear(self) -> int:
        count = len(self._entries)
        self._entries = []
        self._save()
        return count
