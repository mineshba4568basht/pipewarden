"""CLI sub-command: `pipewarden trend` — show run trend statistics."""
from __future__ import annotations

import argparse
import sys

from pipewarden.history import HistoryStore
from pipewarden.trend import TrendSummary, analyse_trend

_DEFAULT_HISTORY_PATH = ".pipewarden_history.json"
_DEFAULT_LIMIT = 20
_FAILURE_THRESHOLD = 3  # consecutive failures before exit code 1


def build_trend_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the *trend* sub-command on *parent*."""
    parser: argparse.ArgumentParser = parent.add_parser(
        "trend",
        help="Show pass-rate and failure streak from run history.",
    )
    parser.add_argument(
        "--history",
        default=_DEFAULT_HISTORY_PATH,
        metavar="FILE",
        help="Path to history JSON file (default: %(default)s).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=_DEFAULT_LIMIT,
        metavar="N",
        help="Number of recent runs to analyse (default: %(default)s).",
    )
    parser.add_argument(
        "--fail-on-streak",
        type=int,
        default=_FAILURE_THRESHOLD,
        metavar="N",
        help="Exit with code 1 when consecutive failures >= N (default: %(default)s).",
    )
    parser.set_defaults(func=handle_trend)
    return parser


def _print_summary(summary: TrendSummary) -> None:
    print(f"  Total runs analysed : {summary.total_runs}")
    print(f"  Passed              : {summary.passed_runs}")
    print(f"  Failed              : {summary.failed_runs}")
    print(f"  Pass rate           : {summary.pass_rate:.1%}")
    print(f"  Consecutive failures: {summary.consecutive_failures}")
    print(f"  Last status         : {summary.last_status or 'n/a'}")


def handle_trend(args: argparse.Namespace) -> int:
    """Entry-point called by the CLI dispatcher."""
    store = HistoryStore(path=args.history)
    summary = analyse_trend(store, limit=args.limit)

    print("=== Pipeline Trend ===")
    _print_summary(summary)

    if summary.total_runs == 0:
        print("No history found.")
        return 0

    if summary.consecutive_failures >= args.fail_on_streak:
        print(
            f"\n[WARN] {summary.consecutive_failures} consecutive failures "
            f">= threshold ({args.fail_on_streak}). Exiting with code 1.",
            file=sys.stderr,
        )
        return 1

    return 0
