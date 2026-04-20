"""CLI helpers for the partitioning feature."""
from __future__ import annotations

import argparse
from typing import List

from pipewarden.partitioning import partition_by_pipeline, partition_by_severity
from pipewarden.runner import AlertEvent


def build_partitioning_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("partition", help="Partition alert events by a key")
    sub = p.add_subparsers(dest="partition_cmd", required=True)

    info = sub.add_parser("info", help="Show partitioning info for a set of events")
    info.add_argument(
        "--by",
        choices=["pipeline", "severity"],
        default="pipeline",
        help="Key to partition by (default: pipeline)",
    )
    p.set_defaults(func=handle_partitioning)


def handle_partitioning(args: argparse.Namespace, events: List[AlertEvent]) -> None:
    """Handle the 'partition' subcommand."""
    by = getattr(args, "by", "pipeline")
    if by == "severity":
        result = partition_by_severity(events)
    else:
        result = partition_by_pipeline(events)

    print(f"Partitioned {result.total_events} event(s) into {len(result.partitions)} partition(s) by '{by}':")
    for name in result.partition_names:
        part = result.partitions[name]
        print(f"  {name}: {part.count} event(s)")
