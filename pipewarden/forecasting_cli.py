"""CLI sub-commands for metric forecasting."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipewarden.forecasting import forecast
from pipewarden.history import HistoryStore


def build_forecasting_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # noqa: SLF001
    p = subparsers.add_parser("forecast", help="Forecast future metric values")
    sub = p.add_subparsers(dest="forecast_cmd")

    run_p = sub.add_parser("run", help="Run a forecast for a pipeline/metric")
    run_p.add_argument("--pipeline", required=True, help="Pipeline name")
    run_p.add_argument("--metric", required=True, help="Metric name")
    run_p.add_argument(
        "--horizon", type=int, default=24, help="Forecast horizon in hours (default: 24)"
    )
    run_p.add_argument(
        "--min-points", type=int, default=3, dest="min_points",
        help="Minimum history points required (default: 3)",
    )
    run_p.add_argument(
        "--history-file", default="pipewarden_history.json", dest="history_file",
        help="Path to history JSON file",
    )
    run_p.add_argument(
        "--json", action="store_true", help="Output result as JSON"
    )

    p.set_defaults(func=handle_forecasting)
    return p


def handle_forecasting(args: argparse.Namespace) -> None:
    if args.forecast_cmd == "run":
        _cmd_run(args)
    else:
        print("Use 'forecast run --help' for usage.")


def _cmd_run(args: argparse.Namespace) -> None:
    store = HistoryStore(Path(args.history_file))
    entries = store.all()
    result = forecast(
        pipeline=args.pipeline,
        metric=args.metric,
        history=entries,
        horizon_hours=args.horizon,
        min_points=args.min_points,
    )
    if args.json:
        print(json.dumps({
            "pipeline": result.pipeline,
            "metric": result.metric,
            "horizon_hours": result.horizon_hours,
            "predicted_value": result.predicted_value,
            "confidence": result.confidence,
            "warning": result.warning,
            "forecasted_at": result.forecasted_at.isoformat(),
        }))
    else:
        print(result)
