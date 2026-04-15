"""CLI sub-commands for the replay feature."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from pipewarden.history import HistoryStore
from pipewarden.replay import replay

_DT_FMT = "%Y-%m-%dT%H:%M:%S"


def build_replay_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("replay", help="Replay historical pipeline runs")
    sub = p.add_subparsers(dest="replay_cmd", required=True)

    run_p = sub.add_parser("run", help="Replay runs for a pipeline in a time window")
    run_p.add_argument("pipeline", help="Pipeline name")
    run_p.add_argument(
        "--start",
        required=True,
        help=f"Start datetime ({_DT_FMT})",
    )
    run_p.add_argument(
        "--end",
        default=None,
        help=f"End datetime ({_DT_FMT}), defaults to now",
    )
    run_p.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum entries to consider (default: 100)",
    )
    run_p.add_argument(
        "--history-file",
        default=".pipewarden_history.json",
        help="Path to history file",
    )


def _parse_dt(value: str) -> datetime:
    return datetime.strptime(value, _DT_FMT).replace(tzinfo=timezone.utc)


def handle_replay(args: argparse.Namespace) -> None:
    if args.replay_cmd == "run":
        _cmd_run(args)


def _cmd_run(args: argparse.Namespace) -> None:
    store = HistoryStore(path=args.history_file)
    start = _parse_dt(args.start)
    end = _parse_dt(args.end) if args.end else datetime.now(tz=timezone.utc)

    result = replay(store, pipeline=args.pipeline, start=start, end=end, limit=args.limit)

    print(result)
    if result.total == 0:
        print("  No entries found in the given time window.")
        return

    for entry in result.entries:
        status = "PASS" if entry.passed else "FAIL"
        print(f"  [{status}] {entry.recorded_at.isoformat()}")
