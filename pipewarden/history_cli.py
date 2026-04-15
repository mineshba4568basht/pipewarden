"""CLI sub-commands for interacting with run history."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from pipewarden.history import DEFAULT_HISTORY_PATH, HistoryStore


def build_history_parser(subparsers) -> None:
    """Register the 'history' sub-command onto an existing subparsers action."""
    hist = subparsers.add_parser("history", help="View or manage run history")
    hist_sub = hist.add_subparsers(dest="history_cmd")

    # list
    ls = hist_sub.add_parser("list", help="List recent runs")
    ls.add_argument("-n", "--limit", type=int, default=10, help="Max entries to show")
    ls.add_argument(
        "--history-file",
        type=Path,
        default=DEFAULT_HISTORY_PATH,
        help="Path to history file",
    )

    # clear
    clr = hist_sub.add_parser("clear", help="Delete all stored history")
    clr.add_argument(
        "--history-file",
        type=Path,
        default=DEFAULT_HISTORY_PATH,
        help="Path to history file",
    )


def handle_history(args: argparse.Namespace) -> int:
    """Dispatch history sub-commands. Returns exit code."""
    if args.history_cmd == "list":
        return _cmd_list(args)
    if args.history_cmd == "clear":
        return _cmd_clear(args)
    print("No history sub-command given. Use 'list' or 'clear'.", file=sys.stderr)
    return 1


def _cmd_list(args: argparse.Namespace) -> int:
    store = HistoryStore(path=args.history_file)
    entries = store.load(limit=args.limit)
    if not entries:
        print("No run history found.")
        return 0
    for entry in entries:
        print(entry)
    return 0


def _cmd_clear(args: argparse.Namespace) -> int:
    store = HistoryStore(path=args.history_file)
    store.clear()
    print("Run history cleared.")
    return 0
