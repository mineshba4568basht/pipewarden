"""CLI sub-commands for anomaly detection."""
from __future__ import annotations

import argparse
import json
import sys

from pipewarden.anomaly import detect_anomaly


def build_anomaly_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser("anomaly", help="Anomaly detection utilities")
    sub = p.add_subparsers(dest="anomaly_cmd", required=True)

    check = sub.add_parser("check", help="Check a single metric value for anomalies")
    check.add_argument("pipeline", help="Pipeline name")
    check.add_argument("metric", help="Metric name")
    check.add_argument("value", type=float, help="Current metric value")
    check.add_argument(
        "--history",
        nargs="+",
        type=float,
        default=[],
        metavar="N",
        help="Historical values (space-separated)",
    )
    check.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        help="Z-score threshold for anomaly (default: 3.0)",
    )
    check.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output result as JSON",
    )
    return p


def handle_anomaly(args: argparse.Namespace) -> None:
    if args.anomaly_cmd == "check":
        _cmd_check(args)


def _cmd_check(args: argparse.Namespace) -> None:
    result = detect_anomaly(
        pipeline=args.pipeline,
        metric=args.metric,
        value=args.value,
        history=args.history,
        threshold=args.threshold,
    )

    if args.output_json:
        data = {
            "pipeline": result.pipeline,
            "metric": result.metric,
            "value": result.value,
            "mean": result.mean,
            "stddev": result.stddev,
            "z_score": result.z_score,
            "threshold": result.threshold,
            "is_anomaly": result.is_anomaly,
        }
        print(json.dumps(data, indent=2))
    else:
        print(result)

    if result.is_anomaly:
        sys.exit(1)
