"""Archiving: move old history entries to a compressed archive store."""
from __future__ import annotations

import json
import gzip
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List


@dataclass
class ArchivePolicy:
    """Configuration for the archiving behaviour."""
    max_age_hours: int = 168  # 7 days
    archive_path: str = ".pipewarden_archive.jsonl.gz"

    def __post_init__(self) -> None:
        if self.max_age_hours < 1:
            raise ValueError("max_age_hours must be >= 1")

    def __str__(self) -> str:
        return (
            f"ArchivePolicy(max_age_hours={self.max_age_hours}, "
            f"archive_path={self.archive_path!r})"
        )


@dataclass
class ArchiveResult:
    """Result of an archive operation."""
    archived: int
    remaining: int
    archive_path: str
    ran_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total(self) -> int:
        return self.archived + self.remaining

    def __str__(self) -> str:
        status = "ok" if self.archived >= 0 else "error"
        return (
            f"[{status}] archived={self.archived} remaining={self.remaining} "
            f"path={self.archive_path!r}"
        )


def archive_entries(
    entries: List[dict],
    policy: ArchivePolicy,
    now: datetime | None = None,
) -> ArchiveResult:
    """Split *entries* into current and archived sets, appending old ones to
    the gzip archive file defined in *policy*.

    Returns an :class:`ArchiveResult` describing what happened.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    cutoff_ts = now.timestamp() - policy.max_age_hours * 3600

    current: List[dict] = []
    to_archive: List[dict] = []

    for entry in entries:
        ts = entry.get("timestamp", 0)
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts).timestamp()
            except ValueError:
                ts = 0
        if ts < cutoff_ts:
            to_archive.append(entry)
        else:
            current.append(entry)

    if to_archive:
        path = Path(policy.archive_path)
        with gzip.open(path, "ab") as fh:
            for rec in to_archive:
                fh.write((json.dumps(rec) + "\n").encode())

    return ArchiveResult(
        archived=len(to_archive),
        remaining=len(current),
        archive_path=policy.archive_path,
    )
