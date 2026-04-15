"""Run history storage and retrieval for pipewarden."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_PATH = Path.home() / ".pipewarden" / "history.json"


@dataclass
class HistoryEntry:
    """A single recorded pipeline run."""

    run_id: str
    timestamp: str
    config_path: str
    passed: bool
    total_checks: int
    failed_checks: int
    alert_count: int

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{self.timestamp}] {status} "
            f"checks={self.total_checks} failed={self.failed_checks} "
            f"alerts={self.alert_count} (run={self.run_id})"
        )


class HistoryStore:
    """Persists and retrieves run history from a JSON file."""

    def __init__(self, path: Path = DEFAULT_HISTORY_PATH) -> None:
        self.path = Path(path)

    def _load_raw(self) -> List[dict]:
        if not self.path.exists():
            return []
        with open(self.path, "r") as fh:
            return json.load(fh)

    def _save_raw(self, records: List[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as fh:
            json.dump(records, fh, indent=2)

    def append(self, entry: HistoryEntry) -> None:
        """Append a new entry to the history file."""
        records = self._load_raw()
        records.append(asdict(entry))
        self._save_raw(records)

    def load(self, limit: Optional[int] = None) -> List[HistoryEntry]:
        """Return stored entries, newest first, optionally limited."""
        records = self._load_raw()
        entries = [HistoryEntry(**r) for r in reversed(records)]
        return entries[:limit] if limit is not None else entries

    def clear(self) -> None:
        """Remove all stored history."""
        if self.path.exists():
            self.path.unlink()


def make_entry(run_id: str, config_path: str, report) -> HistoryEntry:
    """Build a HistoryEntry from a RunReport."""
    return HistoryEntry(
        run_id=run_id,
        timestamp=datetime.utcnow().isoformat(timespec="seconds"),
        config_path=config_path,
        passed=report.passed,
        total_checks=len(report.results),
        failed_checks=len(report.failed_checks),
        alert_count=len(report.alert_events),
    )
