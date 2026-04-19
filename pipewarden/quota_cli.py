"""CLI sub-commands for quota management."""
from __future__ import annotations

import argparse

from pipewarden.quota import QuotaManager, QuotaPolicy


def build_quota_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("quota", help="Manage alert quotas")
    sub = p.add_subparsers(dest="quota_cmd", required=True)

    info = sub.add_parser("info", help="Show quota policy")
    info.add_argument("--max-alerts", type=int, default=10)
    info.add_argument("--window", type=int, default=60, dest="window_minutes")

    reset = sub.add_parser("reset", help="Reset quota for a pipeline")
    reset.add_argument("pipeline")

    p.set_defaults(func=handle_quota)


def handle_quota(args: argparse.Namespace) -> None:
    if args.quota_cmd == "info":
        policy = QuotaPolicy(
            max_alerts=args.max_alerts,
            window_minutes=args.window_minutes,
        )
        print(policy)
    elif args.quota_cmd == "reset":
        mgr = QuotaManager()
        mgr.reset(args.pipeline)
        print(f"Quota reset for pipeline '{args.pipeline}'")
