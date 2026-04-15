"""CLI sub-commands for digest report generation."""
from __future__ import annotations

import argparse
import sys

from pipewarden.digest import build_digest
from pipewarden.history import HistoryStore


def build_digest_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the 'digest' sub-command."""
    parser = subparsers.add_parser(
        "digest",
        help="Generate a periodic health digest from run history",
    )
    parser.add_argument(
        "--history-file",
        default=".pipewarden_history.json",
        help="Path to the history JSON file (default: .pipewarden_history.json)",
    )
    parser.add_argument(
        "--period",
        type=int,
        default=24,
        metavar="HOURS",
        help="Look-back window in hours (default: 24)",
    )
    parser.add_argument(
        "--pipeline",
        default=None,
        help="Filter digest to a single pipeline name",
    )
    parser.set_defaults(func=handle_digest)
    return parser


def handle_digest(args: argparse.Namespace) -> None:
    """Entry-point called by the CLI dispatcher."""
    store = HistoryStore(path=args.history_file)
    report = build_digest(store, period_hours=args.period)

    if args.pipeline:
        report.entries = [
            e for e in report.entries if e.pipeline == args.pipeline
        ]

    if not report.entries:
        print("No history found for the requested period.", file=sys.stderr)
        sys.exit(0)

    print(report)

    if report.degraded_pipelines:
        sys.exit(1)
