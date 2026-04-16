"""CLI sub-commands for alert throttle management."""
from __future__ import annotations
import argparse
from pipewarden.throttle import ThrottleManager, ThrottlePolicy


def build_throttle_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser("throttle", help="Manage alert throttle state")
    sub = p.add_subparsers(dest="throttle_cmd", required=True)

    lst = sub.add_parser("list", help="List active throttle records")
    lst.set_defaults(throttle_cmd="list")

    clr = sub.add_parser("clear", help="Clear throttle for a pipeline/check")
    clr.add_argument("pipeline", help="Pipeline name")
    clr.add_argument("check", help="Check name")

    info = sub.add_parser("info", help="Show throttle policy info")
    info.add_argument("--cooldown", type=int, default=30, help="Cooldown minutes (default 30)")

    return p


def handle_throttle(args: argparse.Namespace, manager: ThrottleManager | None = None) -> None:
    if manager is None:
        manager = ThrottleManager()

    cmd = args.throttle_cmd
    if cmd == "list":
        records = manager.active_records()
        if not records:
            print("No active throttle records.")
        for rec in records:
            print(rec)
    elif cmd == "clear":
        manager.clear(args.pipeline, args.check)
        print(f"Cleared throttle for {args.pipeline}/{args.check}")
    elif cmd == "info":
        policy = ThrottlePolicy(cooldown_minutes=args.cooldown)
        print(f"ThrottlePolicy(cooldown={policy.cooldown_minutes}m max_suppressed={policy.max_suppressed})")
