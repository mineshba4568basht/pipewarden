"""CLI helpers for webhook testing."""
from __future__ import annotations

import argparse

from pipewarden.webhook import WebhookConfig, send_webhook
from pipewarden.runner import AlertEvent
from pipewarden.config import AlertRule
from datetime import datetime


def build_webhook_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser("webhook", help="Webhook notification utilities")
    sub = p.add_subparsers(dest="webhook_cmd")

    test_p = sub.add_parser("test", help="Send a test webhook payload")
    test_p.add_argument("url", help="Webhook URL")
    test_p.add_argument("--secret", default=None, help="Optional shared secret")
    test_p.add_argument("--timeout", type=int, default=10)
    test_p.add_argument("--pipeline", default="test-pipeline")
    test_p.add_argument("--check", default="row_count")
    test_p.add_argument("--severity", default="warning")
    p.set_defaults(func=handle_webhook)
    return p


def handle_webhook(args: argparse.Namespace) -> None:
    if args.webhook_cmd == "test":
        _cmd_test(args)
    else:
        print("No webhook subcommand given. Use 'webhook test'.")


def _cmd_test(args: argparse.Namespace) -> None:
    config = WebhookConfig(url=args.url, secret=args.secret, timeout=args.timeout)
    rule = AlertRule(pipeline=args.pipeline, check_name=args.check, severity=args.severity)
    event = AlertEvent(
        rule=rule,
        message=f"Test webhook from pipewarden [{args.pipeline}/{args.check}]",
        triggered_at=datetime.utcnow(),
    )
    result = send_webhook(event, config)
    print(result)
