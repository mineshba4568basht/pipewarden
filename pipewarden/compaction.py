"""Compaction module: merge and deduplicate history entries to reduce storage."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from pipewarden.history import HistoryEntry, HistoryStore


@dataclass
class CompactionPolicy:
    """Policy controlling how history compaction is performed."""

    max_entries: int = 1000
    keep_failures: bool = True  # always retain failed entries
    dedupe_window_seconds: int = 60

    def __post_init__(self) -> None:
        if self.max_entries < 1:
            raise ValueError("max_entries must be >= 1")
        if self.dedupe_window_seconds < 0:
            raise ValueError("dedupe_window_seconds must be >= 0")

    def __str__(self) -> str:
        return (
            f"CompactionPolicy(max_entries={self.max_entries}, "
            f"keep_failures={self.keep_failures}, "
            f"dedupe_window_seconds={self.dedupe_window_seconds})"
        )


@dataclass
class CompactionResult:
    """Result of a compaction run."""

    original_count: int
    retained_count: int
    removed_count: int
    compacted_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def reduction_pct(self) -> float:
        if self.original_count == 0:
            return 0.0
        return round(self.removed_count / self.original_count * 100, 2)

    def __str__(self) -> str:
        return (
            f"CompactionResult(original={self.original_count}, "
            f"retained={self.retained_count}, "
            f"removed={self.removed_count}, "
            f"reduction={self.reduction_pct}%)"
        )


def _dedupe(entries: List[HistoryEntry], window_seconds: int) -> List[HistoryEntry]:
    """Remove consecutive duplicate pass entries within the deduplication window."""
    if not entries:
        return []
    result: List[HistoryEntry] = [entries[0]]
    for entry in entries[1:]:
        prev = result[-1]
        if (
            entry.passed
            and prev.passed
            and entry.pipeline == prev.pipeline
            and entry.check_name == prev.check_name
        ):
            diff = abs(
                (entry.recorded_at - prev.recorded_at).total_seconds()
            )
            if diff <= window_seconds:
                continue
        result.append(entry)
    return result


def compact(store: HistoryStore, policy: CompactionPolicy) -> CompactionResult:
    """Apply compaction policy to a HistoryStore in place."""
    raw: List[HistoryEntry] = store.recent(limit=10_000)
    original_count = len(raw)

    after_dedupe = _dedupe(raw, policy.dedupe_window_seconds)

    if policy.keep_failures:
        failures = [e for e in after_dedupe if not e.passed]
        passes = [e for e in after_dedupe if e.passed]
        slots = max(0, policy.max_entries - len(failures))
        retained = failures + passes[-slots:] if slots > 0 else failures
    else:
        retained = after_dedupe[-policy.max_entries:]

    retained_count = len(retained)
    removed_count = original_count - retained_count

    store._entries = retained  # type: ignore[attr-defined]

    return CompactionResult(
        original_count=original_count,
        retained_count=retained_count,
        removed_count=removed_count,
    )
