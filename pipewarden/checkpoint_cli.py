"""CLI subcommand for checkpoint management."""
from __future__ import annotations
import argparse
from datetime import datetime
from pipewarden.checkpoint import CheckpointEntry, CheckpointStore


def build_checkpoint_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("checkpoint", help="Manage pipeline checkpoints")
    sub = p.add_subparsers(dest="checkpoint_cmd", required=True)

    ls = sub.add_parser("list", help="List recent checkpoints")
    ls.add_argument("--limit", type=int, default=20)
    ls.add_argument("--pipeline", default=None)

    rec = sub.add_parser("record", help="Record a checkpoint manually")
    rec.add_argument("pipeline")
    rec.add_argument("check_name")
    rec.add_argument("value", type=float)
    rec.add_argument("--status", choices=["pass", "fail"], default="pass")

    sub.add_parser("clear", help="Clear all checkpoints")

    p.set_defaults(func=handle_checkpoint)


def handle_checkpoint(args: argparse.Namespace, store: CheckpointStore | None = None) -> None:
    if store is None:
        store = CheckpointStore()
    cmd = args.checkpoint_cmd
    if cmd == "list":
        _cmd_list(args, store)
    elif cmd == "record":
        _cmd_record(args, store)
    elif cmd == "clear":
        removed = store.clear()
        print(f"Cleared {removed} checkpoint(s).")


def _cmd_list(args: argparse.Namespace, store: CheckpointStore) -> None:
    entries = store.all_entries(limit=args.limit)
    if args.pipeline:
        entries = [e for e in entries if e.pipeline == args.pipeline]
    if not entries:
        print("No checkpoints found.")
        return
    for e in entries:
        print(e)


def _cmd_record(args: argparse.Namespace, store: CheckpointStore) -> None:
    entry = CheckpointEntry(
        pipeline=args.pipeline,
        check_name=args.check_name,
        status=args.status,
        value=args.value,
    )
    store.record(entry)
    print(f"Recorded: {entry}")
