"""CLI helpers for testing notification channels."""
from __future__ import annotations

import argparse
import sys

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.config import AlertRule, load_config
from pipewarden.notifications import NotificationDispatcher
from pipewarden.runner import AlertEvent


def build_notifications_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    parser = parent.add_parser(
        "notify-test",
        help="Send a test notification to configured channels",
    )
    parser.add_argument(
        "--config",
        default="pipewarden.yaml",
        help="Path to config file (default: pipewarden.yaml)",
    )
    parser.add_argument(
        "--slack-webhook",
        dest="slack_webhook",
        default=None,
        help="Slack incoming webhook URL (overrides config)",
    )
    parser.add_argument(
        "--severity",
        default="warning",
        choices=["warning", "critical"],
        help="Severity level for the test event (default: warning)",
    )
    return parser


def handle_notify_test(args: argparse.Namespace) -> int:
    """Send a synthetic through all configured channels."""
    webhook = args.slack_webhook

    if not webhook:
        try:
            cfg = load_config(args.config)
            webhook = getattr(cfg, "slack_webhook", None)
        except FileNotFoundError:
            pass

    if not webhook:
        print(
            "No notification channels configured. "
            "Pass --slack-webhook or set slack_webhook in your config.",
            file=sys.stderr,
        )
        return 1

    rule = AlertRule(name="test-rule", check="check_row_count", threshold=0, severity=args.severity)
    result = CheckResult(
        check_name="check_row_count",
        status=CheckStatus.FAIL,
        message="This is a test notification from PipeWarden.",
    )
    event = AlertEvent(rule=rule, result=result)

    dispatcher = NotificationDispatcher(slack_webhook=webhook)
    results = dispatcher.dispatch(event)

    for r in results:
        print(r)

    failed = [r for r in results if not r.success]
    return 1 if failed else 0
