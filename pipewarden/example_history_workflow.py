"""Example showing how the history module integrates with the runner.

This script demonstrates recording a run result into the history store
and then reading it back — useful as a developer reference.

Run with:  python -m pipewarden.example_history_workflow
"""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock

from pipewarden.history import HistoryStore, make_entry


def _fake_report(passed: bool, total: int, failed: int, alerts: int) -> MagicMock:
    report = MagicMock()
    report.passed = passed
    report.results = [MagicMock()] * total
    report.failed_checks = [MagicMock()] * failed
    report.alert_events = [MagicMock()] * alerts
    return report


def main() -> None:
    store = HistoryStore(path=Path("/tmp/pipewarden_example_history.json"))
    store.clear()

    runs = [
        _fake_report(True, 6, 0, 0),
        _fake_report(False, 6, 2, 1),
        _fake_report(True, 6, 0, 0),
    ]

    print("Recording 3 example runs...")
    for report in runs:
        entry = make_entry(
            run_id=str(uuid.uuid4())[:8],
            config_path="pipewarden/example_config.yaml",
            report=report,
        )
        store.append(entry)
        print(f"  Stored: {entry}")

    print("\nLoading history (newest first):")
    for entry in store.load():
        print(f"  {entry}")

    print("\nLoading with limit=2:")
    for entry in store.load(limit=2):
        print(f"  {entry}")

    store.clear()
    print("\nHistory cleared.")


if __name__ == "__main__":
    main()
