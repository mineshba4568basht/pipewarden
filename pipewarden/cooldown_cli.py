"""CLI subcommand: cooldown management."""
from __future__ import annotations
import argparse
from datetime import datetime
from pipewarden.cooldown import CooldownManager


def build_cooldown_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser("cooldown", help="Manage alert cooldowns")
    sub = p.add_subparsers(dest="cooldown_cmd")

    lst = sub.add_parser("list", help="List active cooldown entries")
    lst.set_defaults(cooldown_cmd="list")

    clr = sub.add_parser("clear", help="Clear cooldown for a pipeline/check")
    clr.add_argument("--pipeline", required=True)
    clr.add_argument("--check", required=True)

    p.set_defaults(func=handle_cooldown)
    return p


def handle_cooldown(args: argparse.Namespace, manager: CooldownManager) -> None:
    cmd = getattr(args, "cooldown_cmd", None)
    if cmd == "list":
        entries = manager.all_entries()
        if not entries:
            print("No active cooldown entries.")
        for e in entries:
            print(e)
    elif cmd == "clear":
        removed = manager.clear(args.pipeline, args.check)
        if removed:
            print(f"Cleared cooldown for {args.pipeline}/{args.check}.")
        else:
            print(f"No cooldown found for {args.pipeline}/{args.check}.")
    else:
        print("Specify a subcommand: list, clear")
