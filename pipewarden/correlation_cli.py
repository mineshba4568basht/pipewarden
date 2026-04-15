"""CLI sub-command for pipeline correlation analysis."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewarden.correlation import correlate_pipelines
from pipewarden.history import HistoryStore


def build_correlation_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'correlation' sub-command."""
    parser = subparsers.add_parser(
        "correlation",
        help="Analyse failure correlations between pipelines.",
    )
    sub = parser.add_subparsers(dest="correlation_cmd", required=True)

    analyse = sub.add_parser("analyse", help="Print pairwise correlation scores.")
    analyse.add_argument(
        "--history-file",
        default=".pipewarden_history.json",
        help="Path to history JSON file.",
    )
    analyse.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max history entries per pipeline to consider.",
    )
    analyse.add_argument(
        "--strong-only",
        action="store_true",
        help="Only show pairs with |score| >= 0.7.",
    )

    parser.set_defaults(func=handle_correlation)


def handle_correlation(args: argparse.Namespace) -> None:
    if args.correlation_cmd == "analyse":
        _cmd_analyse(args)


def _cmd_analyse(args: argparse.Namespace) -> None:
    store = HistoryStore(path=Path(args.history_file))
    pairs = correlate_pipelines(store, limit=args.limit)

    if args.strong_only:
        pairs = [p for p in pairs if p.is_strong]

    if not pairs:
        print("No correlation data available.")
        return

    print(f"{'Pipeline A':<25} {'Pipeline B':<25} {'Score':>8}  {'N':>6}  Strong")
    print("-" * 75)
    for pair in pairs:
        strong_marker = "*" if pair.is_strong else ""
        print(
            f"{pair.pipeline_a:<25} {pair.pipeline_b:<25} "
            f"{pair.score:>+8.4f}  {pair.sample_size:>6}  {strong_marker}"
        )
