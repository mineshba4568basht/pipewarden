"""CLI sub-commands for the retention policy feature."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewarden.history import HistoryStore
from pipewarden.retention import RetentionPolicy, PruneResult, apply_retention


def build_retention_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *retention* sub-command tree."""
    p = subparsers.add_parser("retention", help="Manage history retention policy")
    sub = p.add_subparsers(dest="retention_cmd", required=True)

    prune = sub.add_parser("prune", help="Prune history according to policy")
    prune.add_argument(
        "--history-file",
        default=".pipewarden_history.json",
        help="Path to history file (default: .pipewarden_history.json)",
    )
    prune.add_argument(
        "--max-age-hours",
        type=int,
        default=168,
        help="Remove entries older than N hours (default: 168)",
    )
    prune.add_argument(
        "--max-entries",
        type=int,
        default=1000,
        help="Keep at most N most-recent entries (default: 1000)",
    )

    info = sub.add_parser("info", help="Show current policy settings")
    info.add_argument(
        "--max-age-hours", type=int, default=168
    )
    info.add_argument(
        "--max-entries", type=int, default=1000
    )


def handle_retention(args: argparse.Namespace) -> None:
    """Dispatch to the correct retention sub-command handler."""
    if args.retention_cmd == "prune":
        _cmd_prune(args)
    elif args.retention_cmd == "info":
        _cmd_info(args)


def _cmd_prune(args: argparse.Namespace) -> None:
    policy = RetentionPolicy(
        max_age_hours=args.max_age_hours,
        max_entries=args.max_entries,
    )
    store = HistoryStore(path=Path(args.history_file))
    result: PruneResult = apply_retention(store, policy)
    print(
        f"Pruned {result.total_removed} entries "
        f"({result.removed_by_age} by age, {result.removed_by_cap} by cap). "
        f"{result.remaining} remaining."
    )


def _cmd_info(args: argparse.Namespace) -> None:
    policy = RetentionPolicy(
        max_age_hours=args.max_age_hours,
        max_entries=args.max_entries,
    )
    print(policy)
