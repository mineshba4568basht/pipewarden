"""CLI helpers for the batching module."""
from __future__ import annotations
import argparse
from pipewarden.batching import BatchManager, BatchPolicy


def build_batching_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("batch", help="Manage alert batching")
    sub = p.add_subparsers(dest="batch_cmd")

    info = sub.add_parser("info", help="Show current batching policy defaults")
    info.add_argument("--max-size", type=int, default=10)
    info.add_argument("--max-age", type=float, default=60.0)

    sub.add_parser("flush", help="Flush all pending batches")
    p.set_defaults(func=handle_batching)


def handle_batching(args: argparse.Namespace) -> None:
    cmd = getattr(args, "batch_cmd", None)
    if cmd == "info":
        _cmd_info(args)
    elif cmd == "flush":
        _cmd_flush(args)
    else:
        print("Use 'batch info' or 'batch flush'.")


def _cmd_info(args: argparse.Namespace) -> None:
    try:
        policy = BatchPolicy(max_size=args.max_size, max_age_seconds=args.max_age)
        print(f"BatchPolicy: max_size={policy.max_size}, max_age_seconds={policy.max_age_seconds}")
    except ValueError as exc:
        print(f"Invalid policy: {exc}")


def _cmd_flush(args: argparse.Namespace) -> None:
    manager = BatchManager()
    flushed = manager.flush_all()
    print(f"Flushed {len(flushed)} batch(es).")
