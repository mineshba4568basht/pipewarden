"""CLI sub-commands for shadow-mode management."""
from __future__ import annotations

import argparse
from pipewarden.shadowing import ShadowManager, ShadowPolicy


def build_shadowing_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("shadow", help="Shadow-mode evaluation management")
    sp = p.add_subparsers(dest="shadow_cmd")

    info = sp.add_parser("info", help="Show shadow policy info")
    info.add_argument("--log-silent", action="store_true", default=False,
                      help="Whether silent events are also logged")

    lst = sp.add_parser("list", help="List shadow records")
    lst.add_argument("--pipeline", default=None, help="Filter by pipeline name")
    lst.add_argument("--limit", type=int, default=20, help="Max records to show")

    sp.add_parser("clear", help="Clear all shadow records")

    p.set_defaults(func=handle_shadowing)
    return p


def handle_shadowing(args: argparse.Namespace) -> None:
    manager = ShadowManager()

    cmd = getattr(args, "shadow_cmd", None)
    if cmd == "info":
        policy = ShadowPolicy(log_silent=args.log_silent)
        print(str(policy))
    elif cmd == "list":
        records = manager.records(pipeline=args.pipeline)[: args.limit]
        if not records:
            print("No shadow records found.")
        for rec in records:
            print(str(rec))
    elif cmd == "clear":
        removed = manager.clear()
        print(f"Cleared {removed} shadow record(s).")
    else:
        print(manager.summary())
