"""Retention policy: prune history entries older than a given age."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List

from pipewarden.history import HistoryStore, HistoryEntry


@dataclass
class RetentionPolicy:
    """Describes how long history entries should be kept."""

    max_age_hours: int = 168  # 7 days
    max_entries: int = 1000

    def __post_init__(self) -> None:
        if self.max_age_hours <= 0:
            raise ValueError("max_age_hours must be positive")
        if self.max_entries <= 0:
            raise ValueError("max_entries must be positive")

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"RetentionPolicy(max_age_hours={self.max_age_hours}, "
            f"max_entries={self.max_entries})"
        )


@dataclass
class PruneResult:
    """Summary of a prune operation."""

    removed_by_age: int = 0
    removed_by_cap: int = 0
    remaining: int = 0

    @property
    def total_removed(self) -> int:
        return self.removed_by_age + self.removed_by_cap

    def __str__(self) -> str:
        return (
            f"PruneResult(removed={self.total_removed}, "
            f"age={self.removed_by_age}, cap={self.removed_by_cap}, "
            f"remaining={self.remaining})"
        )


def apply_retention(store: HistoryStore, policy: RetentionPolicy) -> PruneResult:
    """Apply *policy* to *store*, removing stale / excess entries in-place."""
    cutoff: datetime = datetime.now(tz=timezone.utc) - timedelta(
        hours=policy.max_age_hours
    )

    entries: List[HistoryEntry] = store.load()

    after_age = [e for e in entries if e.timestamp >= cutoff]
    removed_by_age = len(entries) - len(after_age)

    # Enforce cap: keep the *most recent* max_entries
    if len(after_age) > policy.max_entries:
        after_cap = after_age[-policy.max_entries :]
        removed_by_cap = len(after_age) - len(after_cap)
    else:
        after_cap = after_age
        removed_by_cap = 0

    # Persist pruned list
    store._data = after_cap  # type: ignore[attr-defined]
    store.save(after_cap)  # type: ignore[attr-defined]

    return PruneResult(
        removed_by_age=removed_by_age,
        removed_by_cap=removed_by_cap,
        remaining=len(after_cap),
    )
