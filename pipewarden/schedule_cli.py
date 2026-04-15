"""CLI sub-commands for schedule inspection in pipewarden."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Optional

from pipewarden.schedule import parse_schedule


def build_schedule_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the *schedule* sub-command group."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "schedule",
        help="Inspect and evaluate cron schedule expressions",
    )
    sub = parser.add_subparsers(dest="schedule_cmd", required=True)

    # check sub-command
    check_p = sub.add_parser("check", help="Check whether a cron expression is due now")
    check_p.add_argument("expression", help="Cron expression, e.g. '*/5 * * * *' or @hourly")
    check_p.add_argument(
        "--at",
        metavar="ISO_DATETIME",
        default=None,
        help="Evaluate at this UTC datetime instead of now (ISO 8601)",
    )

    # validate sub-command
    val_p = sub.add_parser("validate", help="Validate a cron expression without evaluating it")
    val_p.add_argument("expression", help="Cron expression to validate")

    return parser


def _parse_at(at_str: Optional[str]) -> Optional[datetime]:
    if at_str is None:
        return None
    dt = datetime.fromisoformat(at_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def handle_schedule(args: argparse.Namespace) -> None:
    """Dispatch schedule sub-commands."""
    if args.schedule_cmd == "check":
        _cmd_check(args)
    elif args.schedule_cmd == "validate":
        _cmd_validate(args)


def _cmd_check(args: argparse.Namespace) -> None:
    try:
        schedule = parse_schedule(args.expression)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return

    at = _parse_at(getattr(args, "at", None))
    due = schedule.is_due(at=at)
    timestamp = (at or datetime.now(tz=timezone.utc)).strftime("%Y-%m-%d %H:%M UTC")
    status = "DUE" if due else "not due"
    print(f"Schedule {schedule} at {timestamp}: {status}")


def _cmd_validate(args: argparse.Namespace) -> None:
    try:
        schedule = parse_schedule(args.expression)
        print(f"[OK] Valid schedule: {schedule}")
    except ValueError as exc:
        print(f"[INVALID] {exc}")
