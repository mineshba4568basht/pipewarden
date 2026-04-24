"""CLI sub-commands for the alert buffer feature."""
from __future__ import annotations

import argparse

from pipewarden.buffering import AlertBuffer, BufferPolicy


def build_buffering_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("buffer", help="Manage alert buffering policy")
    sub = p.add_subparsers(dest="buffer_cmd")

    # info
    info = sub.add_parser("info", help="Show current buffer policy")
    info.add_argument("--max-size", type=int, default=50, help="Max events before flush")
    info.add_argument("--max-age", type=int, default=300, help="Max age in seconds before flush")

    # flush
    flush = sub.add_parser("flush", help="Manually flush a buffer (dry-run)")
    flush.add_argument("--max-size", type=int, default=50)
    flush.add_argument("--max-age", type=int, default=300)
    flush.add_argument("--events", type=int, default=0, help="Simulate N pending events")

    p.set_defaults(func=handle_buffering)


def handle_buffering(args: argparse.Namespace) -> None:
    cmd = getattr(args, "buffer_cmd", None)
    if cmd == "info" or cmd is None:
        _cmd_info(args)
    elif cmd == "flush":
        _cmd_flush(args)
    else:
        print(f"Unknown buffer sub-command: {cmd}")


def _cmd_info(args: argparse.Namespace) -> None:
    try:
        policy = BufferPolicy(max_size=args.max_size, max_age_seconds=args.max_age)
    except ValueError as exc:
        print(f"[error] {exc}")
        return
    buf = AlertBuffer(policy=policy)
    print(str(policy))
    print(str(buf))


def _cmd_flush(args: argparse.Namespace) -> None:
    try:
        policy = BufferPolicy(max_size=args.max_size, max_age_seconds=args.max_age)
    except ValueError as exc:
        print(f"[error] {exc}")
        return
    buf = AlertBuffer(policy=policy)
    print(f"Simulated buffer with {args.events} pending event(s).")
    result = buf.flush()
    if result is None:
        print("Buffer is empty — nothing to flush.")
    else:
        print(str(result))
