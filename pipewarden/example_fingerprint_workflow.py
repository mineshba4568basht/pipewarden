"""Example script demonstrating alert fingerprinting."""
from __future__ import annotations

from unittest.mock import MagicMock

from pipewarden.fingerprint import FingerprintStore


def _fake_event(pipeline: str, check: str, severity: str = "warning") -> MagicMock:
    event = MagicMock()
    event.rule.pipeline = pipeline
    event.rule.severity = severity
    event.result.check_name = check
    return event


def main() -> None:
    store = FingerprintStore()

    events = [
        _fake_event("orders", "row_count", "warning"),
        _fake_event("orders", "row_count", "warning"),  # duplicate
        _fake_event("orders", "null_check", "critical"),
        _fake_event("payments", "row_count", "warning"),
        _fake_event("orders", "row_count", "warning"),  # third occurrence
    ]

    print("Recording events...")
    for ev in events:
        fp = store.record(ev)
        print(f"  -> {fp}")

    print(f"\nUnique fingerprints: {len(store.all())}")
    for fp in store.all():
        print(f"  {fp}")


if __name__ == "__main__":
    main()
