"""CLI commands for managing pipeline metric snapshots."""
from __future__ import annotations

import argparse
from typing import List

from pipewarden.snapshot import SnapshotEntry, SnapshotStore


def build_snapshot_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # noqa: SLF001
    snap = subparsers.add_parser("snapshot", help="Capture and compare pipeline metric snapshots")
    sub = snap.add_subparsers(dest="snap_cmd", required=True)

    # capture
    cap = sub.add_parser("capture", help="Record a metric value")
    cap.add_argument("pipeline", help="Pipeline name")
    cap.add_argument("metric", help="Metric name (e.g. row_count)")
    cap.add_argument("value", type=float, help="Numeric metric value")

    # diff
    dif = sub.add_parser("diff", help="Compare current value against last snapshot")
    dif.add_argument("pipeline", help="Pipeline name")
    dif.add_argument("metric", help="Metric name")
    dif.add_argument("value", type=float, help="Current numeric value")

    # list
    lst = sub.add_parser("list", help="Show latest snapshot per pipeline/metric")
    lst.add_argument("--pipeline", default=None, help="Filter by pipeline name")

    # clear
    sub.add_parser("clear", help="Delete all stored snapshots")

    snap.set_defaults(func=handle_snapshot)
    return snap


def handle_snapshot(args: argparse.Namespace, store: SnapshotStore | None = None) -> None:
    if store is None:
        store = SnapshotStore()

    if args.snap_cmd == "capture":
        _cmd_capture(args, store)
    elif args.snap_cmd == "diff":
        _cmd_diff(args, store)
    elif args.snap_cmd == "list":
        _cmd_list(args, store)
    elif args.snap_cmd == "clear":
        store.clear()
        print("All snapshots cleared.")


def _cmd_capture(args: argparse.Namespace, store: SnapshotStore) -> None:
    entry = SnapshotEntry(pipeline=args.pipeline, metric=args.metric, value=args.value)
    store.save(entry)
    print(f"Captured: {entry}")


def _cmd_diff(args: argparse.Namespace, store: SnapshotStore) -> None:
    diff = store.diff(args.pipeline, args.metric, args.value)
    if diff is None:
        print(f"No previous snapshot found for {args.pipeline}/{args.metric}.")
    else:
        print(diff)


def _cmd_list(args: argparse.Namespace, store: SnapshotStore) -> None:
    seen: set = set()
    entries = []
    for raw in reversed(store._data):  # noqa: SLF001
        key = (raw["pipeline"], raw["metric"])
        if key in seen:
            continue
        if args.pipeline and raw["pipeline"] != args.pipeline:
            continue
        seen.add(key)
        entries.append(SnapshotEntry(**raw))
    if not entries:
        print("No snapshots stored.")
    else:
        for e in sorted(entries, key=lambda x: (x.pipeline, x.metric)):
            print(e)
