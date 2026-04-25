"""CLI sub-commands for watermark management."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Optional

from pipewarden.watermark import WatermarkStore, check_lag


def build_watermark_parser(
    parent: Optional[argparse.ArgumentParser] = None,
) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(prog="pipewarden watermark")
    sub = parser.add_subparsers(dest="watermark_cmd")

    # update
    upd = sub.add_parser("update", help="Advance the watermark for a pipeline")
    upd.add_argument("pipeline", help="Pipeline name")
    upd.add_argument("event_time", help="ISO-8601 event timestamp")

    # lag
    lag_p = sub.add_parser("lag", help="Check current watermark lag")
    lag_p.add_argument("pipeline", help="Pipeline name")
    lag_p.add_argument(
        "--threshold",
        type=float,
        default=300.0,
        metavar="SECONDS",
        help="Lag threshold in seconds (default: 300)",
    )

    # list
    sub.add_parser("list", help="List all tracked watermarks")

    # clear
    clr = sub.add_parser("clear", help="Remove watermark(s)")
    clr.add_argument(
        "--pipeline",
        default=None,
        help="Pipeline to clear (omit to clear all)",
    )

    return parser


def handle_watermark(args: argparse.Namespace, store: WatermarkStore) -> None:
    cmd = getattr(args, "watermark_cmd", None)

    if cmd == "update":
        _cmd_update(args, store)
    elif cmd == "lag":
        _cmd_lag(args, store)
    elif cmd == "list":
        _cmd_list(store)
    elif cmd == "clear":
        _cmd_clear(args, store)
    else:
        print("No watermark sub-command given. Use --help for usage.")


def _cmd_update(args: argparse.Namespace, store: WatermarkStore) -> None:
    try:
        event_time = datetime.fromisoformat(args.event_time).replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        print(f"Invalid event_time: {exc}")
        return
    entry = store.update(args.pipeline, event_time)
    print(f"Watermark updated: {entry}")


def _cmd_lag(args: argparse.Namespace, store: WatermarkStore) -> None:
    result = check_lag(store, args.pipeline, threshold_seconds=args.threshold)
    status = "BREACHED" if result.breached else "OK"
    print(
        f"{args.pipeline}: lag={result.lag_seconds:.1f}s "
        f"threshold={result.threshold_seconds:.1f}s [{status}]"
    )


def _cmd_list(store: WatermarkStore) -> None:
    entries = store.all()
    if not entries:
        print("No watermarks tracked.")
        return
    for entry in entries:
        print(entry)


def _cmd_clear(args: argparse.Namespace, store: WatermarkStore) -> None:
    removed = store.clear(pipeline=args.pipeline)
    target = args.pipeline or "all pipelines"
    print(f"Cleared {removed} watermark(s) for {target}.")
