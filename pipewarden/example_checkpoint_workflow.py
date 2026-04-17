"""Example showing checkpoint record and retrieval workflow."""
from __future__ import annotations
import tempfile, pathlib
from pipewarden.checkpoint import CheckpointEntry, CheckpointStore


def _fake_entry(pipeline: str, check: str, value: float, status: str = "pass") -> CheckpointEntry:
    return CheckpointEntry(pipeline=pipeline, check_name=check, status=status, value=value)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = CheckpointStore(path=str(pathlib.Path(tmp) / "checkpoints.json"))

        # Simulate two pipeline runs
        store.record(_fake_entry("sales_pipeline", "row_count", 1500.0))
        store.record(_fake_entry("sales_pipeline", "null_check", 0.0))
        store.record(_fake_entry("sales_pipeline", "row_count", 1480.0))
        store.record(_fake_entry("inventory_pipeline", "row_count", 300.0, status="fail"))

        print("=== All Checkpoints ===")
        for e in store.all_entries():
            print(" ", e)

        print("\n=== Latest for sales_pipeline/row_count ===")
        latest = store.latest("sales_pipeline", "row_count")
        if latest:
            print(" ", latest)

        print("\n=== Latest for inventory_pipeline/row_count ===")
        inv = store.latest("inventory_pipeline", "row_count")
        if inv:
            print(" ", inv)
            if inv.status == "fail":
                print("  ⚠ Last run failed — investigate before proceeding.")


if __name__ == "__main__":
    main()
