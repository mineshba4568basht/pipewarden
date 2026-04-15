"""Example script demonstrating the correlation analysis workflow."""
from __future__ import annotations

import random
from datetime import datetime, timezone
from pathlib import Path

from pipewarden.correlation import correlate_pipelines
from pipewarden.history import HistoryEntry, HistoryStore


def _fake_entry(pipeline: str, passed: bool) -> HistoryEntry:
    return HistoryEntry(
        pipeline=pipeline,
        run_at=datetime.now(timezone.utc).isoformat(),
        passed=passed,
        total_checks=3,
        failed_checks=0 if passed else 1,
    )


def main() -> None:
    store = HistoryStore(path=Path(".pipewarden_correlation_demo.json"))

    rng = random.Random(42)
    # Simulate 20 runs; pipe_a and pipe_b fail together, pipe_c is independent.
    for _ in range(20):
        shared_fail = rng.random() < 0.3
        store.append(_fake_entry("pipe_a", not shared_fail))
        store.append(_fake_entry("pipe_b", not shared_fail))
        store.append(_fake_entry("pipe_c", rng.random() > 0.3))

    pairs = correlate_pipelines(store, limit=50)

    print("Pipeline Correlation Report")
    print("=" * 50)
    if not pairs:
        print("Not enough data for correlation analysis.")
        return

    for pair in pairs:
        marker = "  [STRONG]" if pair.is_strong else ""
        print(f"  {pair}{marker}")

    print()
    strong = [p for p in pairs if p.is_strong]
    print(f"Strong correlations found: {len(strong)}")


if __name__ == "__main__":
    main()
