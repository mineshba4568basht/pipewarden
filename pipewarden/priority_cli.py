"""CLI helpers for the priority scoring feature."""
from __future__ import annotations
import argparse
from pipewarden.priority import PriorityPolicy


def build_priority_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("priority", help="Score alert priority")
    sub = p.add_subparsers(dest="priority_cmd")

    info = sub.add_parser("info", help="Show current policy settings")
    info.add_argument("--tag-bonus", type=int, default=20)
    info.add_argument("--recurrence-weight", type=int, default=5)
    info.add_argument("--max-recurrence-bonus", type=int, default=50)
    info.add_argument("--high-priority-tags", nargs="*", default=[])

    p.set_defaults(func=handle_priority)
    return p


def handle_priority(args: argparse.Namespace) -> None:
    if args.priority_cmd == "info":
        policy = PriorityPolicy(
            high_priority_tags=args.high_priority_tags,
            tag_bonus=args.tag_bonus,
            recurrence_weight=args.recurrence_weight,
            max_recurrence_bonus=args.max_recurrence_bonus,
        )
        print(f"PriorityPolicy")
        print(f"  high_priority_tags : {policy.high_priority_tags}")
        print(f"  tag_bonus          : {policy.tag_bonus}")
        print(f"  recurrence_weight  : {policy.recurrence_weight}")
        print(f"  max_recurrence_bonus: {policy.max_recurrence_bonus}")
    else:
        print("Use 'priority info' to inspect policy settings.")
