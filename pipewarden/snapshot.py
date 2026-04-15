"""Snapshot module: capture and compare pipeline metric snapshots."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class SnapshotEntry:
    """A single captured metric snapshot."""
    pipeline: str
    metric: str
    value: float
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __str__(self) -> str:
        return f"[{self.captured_at}] {self.pipeline}/{self.metric} = {self.value}"


@dataclass
class SnapshotDiff:
    """Difference between two snapshot values for the same metric."""
    pipeline: str
    metric: str
    previous: float
    current: float

    @property
    def delta(self) -> float:
        return self.current - self.previous

    @property
    def pct_change(self) -> Optional[float]:
        if self.previous == 0:
            return None
        return round((self.delta / self.previous) * 100, 2)

    def __str__(self) -> str:
        pct = f"{self.pct_change:+.2f}%" if self.pct_change is not None else "n/a"
        return (
            f"{self.pipeline}/{self.metric}: "
            f"{self.previous} -> {self.current} ({pct})"
        )


class SnapshotStore:
    """Persist and retrieve metric snapshots from a JSON file."""

    def __init__(self, path: str = ".pipewarden_snapshots.json") -> None:
        self._path = path
        self._data: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        if not os.path.exists(self._path):
            return []
        with open(self._path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)

    def save(self, entry: SnapshotEntry) -> None:
        self._data.append(asdict(entry))
        self._save()

    def latest(self, pipeline: str, metric: str) -> Optional[SnapshotEntry]:
        matches = [
            e for e in self._data
            if e["pipeline"] == pipeline and e["metric"] == metric
        ]
        if not matches:
            return None
        raw = matches[-1]
        return SnapshotEntry(**raw)

    def diff(self, pipeline: str, metric: str, current: float) -> Optional[SnapshotDiff]:
        prev = self.latest(pipeline, metric)
        if prev is None:
            return None
        return SnapshotDiff(
            pipeline=pipeline,
            metric=metric,
            previous=prev.value,
            current=current,
        )

    def clear(self) -> None:
        self._data = []
        self._save()
