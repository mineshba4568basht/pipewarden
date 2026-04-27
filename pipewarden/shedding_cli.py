"""CLI interface for the load-shedding module."""
from __future__ import annotations

import argparse

from pipewarden.shedding import SheddingPolicy


def build_shedding_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("shedding", help="Configure and inspect load-shedding policy")
    sp = p.add_subparsers(dest="shedding_cmd")

    info = sp.add_parser("info", help="Display the current shedding policy")
    info.add_argument(
        "--max-queue-depth",
        type=int,
        default=100,
        dest="max_queue_depth",
        help="Maximum queue depth before shedding activates (default: 100)",
    )
    info.add_argument(
        "--min-priority",
        type=int,
        default=0,
        dest="min_priority",
        help="Minimum priority score to keep (0-10, default: 0)",
    )
    info.add_argument(
        "--no-shed-on-overload",
        action="store_false",
        dest="shed_on_overload",
        default=True,
        help="Disable shedding even when overloaded",
    )

    p.set_defaults(func=handle_shedding)
    return p


def handle_shedding(args: argparse.Namespace) -> None:
    if args.shedding_cmd == "info":
        policy = SheddingPolicy(
            max_queue_depth=args.max_queue_depth,
            min_priority=args.min_priority,
            shed_on_overload=args.shed_on_overload,
        )
        print(policy)
    else:
        print("No shedding sub-command given. Use 'shedding info'.")
