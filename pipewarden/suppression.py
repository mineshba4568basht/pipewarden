"""Alert suppression windows — prevent alerts during planned maintenance."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class SuppressionWindow:
    pipeline: str
    start: datetime
    end: datetime
    reason: str = ""

    def is_active(self, at: Optional[datetime] = None) -> bool:
        now = at or datetime.utcnow()
        return self.start <= now <= self.end

    def covers(self, pipeline: str, at: Optional[datetime] = None) -> bool:
        return self.pipeline == pipeline and self.is_active(at)

    def __str__(self) -> str:
        status = "ACTIVE" if self.is_active() else "INACTIVE"
        return (
            f"SuppressionWindow({self.pipeline!r} "
            f"{self.start.isoformat()} -> {self.end.isoformat()} "
            f"[{status}] reason={self.reason!r})"
        )


@dataclass
class SuppressionManager:
    _windows: List[SuppressionWindow] = field(default_factory=list)

    def add(self, window: SuppressionWindow) -> None:
        self._windows.append(window)

    def is_suppressed(self, pipeline: str, at: Optional[datetime] = None) -> bool:
        return any(w.covers(pipeline, at) for w in self._windows)

    def active_windows(self, at: Optional[datetime] = None) -> List[SuppressionWindow]:
        return [w for w in self._windows if w.is_active(at)]

    def remove_expired(self, at: Optional[datetime] = None) -> int:
        now = at or datetime.utcnow()
        before = len(self._windows)
        self._windows = [w for w in self._windows if w.end >= now]
        return before - len(self._windows)

    def clear(self) -> None:
        self._windows.clear()

    def __len__(self) -> int:
        return len(self._windows)
