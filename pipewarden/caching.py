"""Result caching for pipeline checks to avoid redundant executions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from pipewarden.checks import CheckResult


@dataclass
class CacheEntry:
    result: CheckResult
    cached_at: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: int = 300

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        return now >= self.cached_at + timedelta(seconds=self.ttl_seconds)

    def __str__(self) -> str:  # pragma: no cover
        status = "expired" if self.is_expired() else "valid"
        return (
            f"CacheEntry(pipeline={self.result.rule_name}, "
            f"check={self.result.check_name}, status={status}, "
            f"cached_at={self.cached_at.isoformat()})"
        )


@dataclass
class CachePolicy:
    ttl_seconds: int = 300
    max_entries: int = 256

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if self.max_entries <= 0:
            raise ValueError("max_entries must be positive")

    def __str__(self) -> str:  # pragma: no cover
        return f"CachePolicy(ttl={self.ttl_seconds}s, max_entries={self.max_entries})"


class ResultCache:
    """In-memory LRU-style cache for CheckResult objects."""

    def __init__(self, policy: Optional[CachePolicy] = None) -> None:
        self._policy = policy or CachePolicy()
        self._store: Dict[str, CacheEntry] = {}

    @staticmethod
    def _key(pipeline: str, check: str) -> str:
        return f"{pipeline}::{check}"

    def put(self, result: CheckResult) -> None:
        """Store a result in the cache, evicting oldest entry if at capacity."""
        if len(self._store) >= self._policy.max_entries:
            oldest_key = next(iter(self._store))
            del self._store[oldest_key]
        key = self._key(result.rule_name, result.check_name)
        self._store[key] = CacheEntry(
            result=result, ttl_seconds=self._policy.ttl_seconds
        )

    def get(self, pipeline: str, check: str) -> Optional[CheckResult]:
        """Return cached result if present and not expired, else None."""
        key = self._key(pipeline, check)
        entry = self._store.get(key)
        if entry is None or entry.is_expired():
            if entry is not None:
                del self._store[key]
            return None
        return entry.result

    def invalidate(self, pipeline: str, check: str) -> bool:
        key = self._key(pipeline, check)
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> int:
        count = len(self._store)
        self._store.clear()
        return count

    @property
    def size(self) -> int:
        return len(self._store)
