"""CLI sub-commands for the aggregation feature."""

from __future__ import annotations

import argparse

from pipewarden.aggregation import AggregationPolicy


def build_aggregation_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("aggregation", help="Inspect aggregation policy settings")
    sp = p.add_subparsers(dest="agg_cmd")

    info = sp.add_parser("info", help="Show current aggregation policy defaults")
    info.add_argument("--window", type=int, default=60, help="Window in seconds")
    info.add_argument("--max-events", type=int, default=100, help="Max events per bucket")
    info.add_argument(
        "--group-by",
        choices=["pipeline", "check", "severity"],
        default="pipeline",
        help="Grouping dimension",
    )

    p.set_defaults(func=handle_aggregation)
    return p


def handle_aggregation(args: argparse.Namespace) -> None:  # pragma: no cover
    if args.agg_cmd == "info":
        try:
            policy = AggregationPolicy(
                window_seconds=args.window,
                max_events=args.max_events,
                group_by=args.group_by,
            )
            print(policy)
        except ValueError as exc:
            print(f"[error] {exc}")
    else:
        print("Use 'pipewarden aggregation info --help' for usage.")
