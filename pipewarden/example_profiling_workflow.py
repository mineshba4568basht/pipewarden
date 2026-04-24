"""Example demonstrating the profiling module end-to-end."""
from __future__ import annotations

import random
import time

from pipewarden.profiling import ProfilingStore


def _simulate_check(pipeline: str, check: str, store: ProfilingStore) -> None:
    """Simulate a check run and record its duration."""
    start = time.monotonic()
    # Simulate variable work
    time.sleep(random.uniform(0.005, 0.030))
    elapsed_ms = (time.monotonic() - start) * 1000
    sample = store.record(pipeline, check, round(elapsed_ms, 2))
    print(f"  Recorded: {sample}")


def main() -> None:
    store = ProfilingStore()

    print("=== Simulating pipeline runs ===")
    for _ in range(5):
        _simulate_check("orders_etl", "row_count", store)
    for _ in range(3):
        _simulate_check("orders_etl", "null_check", store)
    for _ in range(4):
        _simulate_check("inventory_etl", "row_count", store)

    print("\n=== Recent samples (limit 6) ===")
    for s in store.all_samples(limit=6):
        print(f"  {s}")

    print("\n=== Report: orders_etl / row_count ===")
    report = store.report("orders_etl", "row_count")
    print(f"  {report}")

    print("\n=== Report: orders_etl / null_check ===")
    report2 = store.report("orders_etl", "null_check")
    print(f"  {report2}")

    print("\n=== Clearing orders_etl samples ===")
    removed = store.clear(pipeline="orders_etl")
    print(f"  Removed {removed} sample(s)")
    print(f"  Remaining: {len(store.all_samples())} sample(s)")


if __name__ == "__main__":
    main()
