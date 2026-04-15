"""CLI sub-commands for baseline management."""
from __future__ import annotations

import argparse
import sys

from pipewarden.baseline import BaselineStore


def build_baseline_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = parent.add_parser("baseline", help="Manage metric baselines for drift detection")
    sub = p.add_subparsers(dest="baseline_cmd", required=True)

    # set
    s = sub.add_parser("set", help="Capture a baseline value")
    s.add_argument("pipeline", help="Pipeline name")
    s.add_argument("metric", help="Metric name")
    s.add_argument("value", type=float, help="Numeric baseline value")

    # get
    g = sub.add_parser("get", help="Retrieve a stored baseline")
    g.add_argument("pipeline")
    g.add_argument("metric")

    # list
    sub.add_parser("list", help="List all stored baselines")

    # drift
    d = sub.add_parser("drift", help="Check current value against baseline")
    d.add_argument("pipeline")
    d.add_argument("metric")
    d.add_argument("current", type=float, help="Current observed value")
    d.add_argument("--threshold", type=float, default=10.0, help="Drift threshold %%  (default: 10)")

    # clear
    sub.add_parser("clear", help="Remove all stored baselines")

    return p


def handle_baseline(args: argparse.Namespace, store: BaselineStore | None = None) -> int:
    if store is None:
        store = BaselineStore()

    cmd = args.baseline_cmd

    if cmd == "set":
        entry = store.set(args.pipeline, args.metric, args.value)
        print(f"Baseline captured: {entry}")
        return 0

    if cmd == "get":
        entry = store.get(args.pipeline, args.metric)
        if entry is None:
            print(f"No baseline found for {args.pipeline}/{args.metric}", file=sys.stderr)
            return 1
        print(entry)
        return 0

    if cmd == "list":
        entries = store.list_entries()
        if not entries:
            print("No baselines stored.")
        else:
            for e in entries:
                print(e)
        return 0

    if cmd == "drift":
        drift = store.check_drift(args.pipeline, args.metric, args.current, args.threshold)
        if drift is None:
            print(f"No baseline for {args.pipeline}/{args.metric} — set one first.", file=sys.stderr)
            return 1
        print(drift)
        return 1 if drift.is_drifted else 0

    if cmd == "clear":
        store.clear()
        print("All baselines cleared.")
        return 0

    return 0
