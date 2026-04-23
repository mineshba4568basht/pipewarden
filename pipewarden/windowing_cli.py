"""CLI sub-commands for the windowing feature."""
from __future__ import annotations

import argparse
from datetime import datetime

from pipewarden.history import HistoryStore
from pipewarden.windowing import WindowPolicy, build_windows


def build_windowing_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("window", help="Aggregate alert events into time windows")
    sp = p.add_subparsers(dest="window_cmd")

    analyse = sp.add_parser("analyse", help="Print window buckets for a pipeline")
    analyse.add_argument("--pipeline", default=None, help="Filter by pipeline name")
    analyse.add_argument(
        "--size", type=int, default=300, dest="size_seconds", help="Window size in seconds"
    )
    analyse.add_argument(
        "--slide",
        type=int,
        default=None,
        dest="slide_seconds",
        help="Slide interval in seconds (omit for tumbling window)",
    )
    analyse.add_argument(
        "--history-file", default=".pipewarden_history.json", dest="history_file"
    )
    p.set_defaults(func=handle_windowing)


def handle_windowing(args: argparse.Namespace) -> None:
    if args.window_cmd == "analyse":
        _cmd_analyse(args)
    else:
        print("No window sub-command specified. Use 'window analyse'.")


def _cmd_analyse(args: argparse.Namespace) -> None:
    store = HistoryStore(path=args.history_file)
    policy = WindowPolicy(
        size_seconds=args.size_seconds,
        slide_seconds=args.slide_seconds,
    )

    # Collect alert events from history entries.
    events = []
    for entry in store.list():
        for evt in entry.alert_events:
            if args.pipeline is None or evt.pipeline == args.pipeline:
                events.append(evt)

    buckets = build_windows(events, policy, reference=datetime.utcnow())

    if not buckets:
        print("No events found for the given filters.")
        return

    print(f"Policy : {policy}")
    print(f"Buckets: {len(buckets)}")
    print()
    for b in buckets:
        print(f"  {b}  pipelines={b.pipelines}")
