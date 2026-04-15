"""Command-line interface for pipewarden."""
import sys
import logging
import argparse
from pathlib import Path

from pipewarden.config import load_config
from pipewarden.checks import check_row_count, check_nulls, check_freshness
from pipewarden.runner import PipelineRunner
from pipewarden.alerts import AlertDispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

CHECK_REGISTRY = {
    "row_count": check_row_count,
    "nulls": check_nulls,
    "freshness": check_freshness,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipewarden",
        description="Validate and monitor data pipeline health.",
    )
    parser.add_argument(
        "--config",
        default="pipewarden.yaml",
        help="Path to the pipewarden config file (default: pipewarden.yaml)",
    )
    parser.add_argument(
        "--channels",
        nargs="+",
        default=["log"],
        help="Alert channels to use (default: log)",
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Enable verbose output",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute the pipeline checks and dispatch alerts. Returns exit code."""
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config_path = Path(args.config)
    logger.info("Loading config from %s", config_path)

    try:
        config = load_config(config_path)
    except FileNotFoundError:
        logger.error("Config file not found: %s", config_path)
        return 2
    except Exception as exc:
        logger.error("Failed to load config: %s", exc)
        return 2

    runner = PipelineRunner(config=config, check_registry=CHECK_REGISTRY)
    report = runner.run()

    dispatcher = AlertDispatcher(channels=args.channels)
    alert_records = dispatcher.dispatch_all(report.alert_events)

    failed_dispatches = dispatcher.failed_dispatches
    if failed_dispatches:
        logger.warning("%d alert(s) failed to dispatch.", len(failed_dispatches))

    logger.info("Run complete. Passed: %s | Checks run: %d", report.passed, len(report.results))

    if not report.passed:
        logger.warning("%d check(s) failed.", len(report.failed_checks))
        return 1

    return 0


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
