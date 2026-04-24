"""Alert buffering — collect events and flush when a threshold or timeout is met."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from pipewarden.runner import AlertEvent


@dataclass
class BufferPolicy:
    """Configuration for the alert buffer."""

    max_size: int = 50
    max_age_seconds: int = 300

    def __post_init__(self) -> None:
        if self.max_size < 1:
            raise ValueError("max_size must be >= 1")
        if self.max_age_seconds < 1:
            raise ValueError("max_age_seconds must be >= 1")

    def __str__(self) -> str:
        return (
            f"BufferPolicy(max_size={self.max_size}, "
            f"max_age_seconds={self.max_age_seconds}s)"
        )


@dataclass
class FlushResult:
    """Outcome of a buffer flush operation."""

    flushed: List[AlertEvent]
    reason: str  # 'size', 'age', or 'manual'

    @property
    def count(self) -> int:
        return len(self.flushed)

    def __str__(self) -> str:
        return f"FlushResult(count={self.count}, reason={self.reason})"


@dataclass
class AlertBuffer:
    """Accumulates AlertEvents and flushes them according to a BufferPolicy."""

    policy: BufferPolicy = field(default_factory=BufferPolicy)
    _events: List[AlertEvent] = field(default_factory=list, init=False)
    _opened_at: Optional[datetime] = field(default=None, init=False)

    def add(self, event: AlertEvent) -> Optional[FlushResult]:
        """Add an event; return a FlushResult if the buffer should be flushed."""
        if self._opened_at is None:
            self._opened_at = datetime.now(timezone.utc)
        self._events.append(event)
        if len(self._events) >= self.policy.max_size:
            return self._flush("size")
        return None

    def check_age(self) -> Optional[FlushResult]:
        """Return a FlushResult if the buffer has exceeded its max age."""
        if not self._events or self._opened_at is None:
            return None
        age = (datetime.now(timezone.utc) - self._opened_at).total_seconds()
        if age >= self.policy.max_age_seconds:
            return self._flush("age")
        return None

    def flush(self) -> Optional[FlushResult]:
        """Manually flush the buffer regardless of policy."""
        if not self._events:
            return None
        return self._flush("manual")

    def _flush(self, reason: str) -> FlushResult:
        result = FlushResult(flushed=list(self._events), reason=reason)
        self._events.clear()
        self._opened_at = None
        return result

    @property
    def pending(self) -> int:
        return len(self._events)

    def __str__(self) -> str:
        return f"AlertBuffer(pending={self.pending}, policy={self.policy})"
