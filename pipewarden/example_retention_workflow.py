"""Runnable example demonstrating the retention feature end-to-end."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

from pipewarden.history import HistoryEntry, HistoryStore
from pipewarden.retention import RetentionPolicy, apply_retention


def _fake_entry(hours_ago: float, pipeline: str = "demo") -> HistoryEntry:
    ts = datetime.now(tz=timezone.utc) - timedelta(hours=hours_ago)
    return HistoryEntry(
        pipeline=pipeline,
        passed=hours_ago < 50,
        timestamp=ts,
        checks_run=3,
        checks_failed=0 if hours_ago < 50 else 1,
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store = HistoryStore(path=Path(tmpdir) / "history.json")

        # Seed: 5 old entries (>168 h) + 10 recent entries
        entries = [_fake_entry(h) for h in [200, 190, 180, 175, 170]] + [
            _fake_entry(h) for h in range(1, 11)
        ]
        store.save(entries)
        print(f"Seeded {len(entries)} entries into history store.")

        # Apply a policy that removes entries older than 168 h and caps at 7
        policy = RetentionPolicy(max_age_hours=168, max_entries=7)
        print(f"Applying policy: {policy}")

        result = apply_retention(store, policy)
        print(result)

        remaining = store.load()
        print(f"\nRemaining entries ({len(remaining)}):")
        for e in remaining:
            status = "PASS" if e.passed else "FAIL"
            age_h = round(
                (datetime.now(tz=timezone.utc) - e.timestamp).total_seconds() / 3600, 1
            )
            print(f"  [{status}] {e.pipeline} — {age_h}h ago")


if __name__ == "__main__":
    main()
