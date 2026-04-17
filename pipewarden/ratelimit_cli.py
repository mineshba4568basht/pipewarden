"""CLI sub-commands for rate-limit inspection and management."""
from __future__ import annotations
import argparse

from pipewarden.ratelimit import RateLimiter, RateLimitPolicy


def build_ratelimit_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("ratelimit", help="Manage alert rate limiting")
    sub = p.add_subparsers(dest="ratelimit_cmd", required=True)

    info = sub.add_parser("info", help="Show current policy")
    info.add_argument("--max-alerts", type=int, default=5)
    info.add_argument("--window", type=int, default=300)

    reset = sub.add_parser("reset", help="Reset counters for a pipeline")
    reset.add_argument("pipeline", help="Pipeline name to reset")

    sub.add_parser("reset-all", help="Reset all rate-limit counters")

    p.set_defaults(func=handle_ratelimit)


def handle_ratelimit(args: argparse.Namespace) -> None:
    if args.ratelimit_cmd == "info":
        policy = RateLimitPolicy(
            max_alerts=args.max_alerts,
            window_seconds=args.window,
        )
        print(policy)
    elif args.ratelimit_cmd == "reset":
        limiter = RateLimiter()
        limiter.reset(args.pipeline)
        print(f"Rate-limit counters cleared for pipeline: {args.pipeline}")
    elif args.ratelimit_cmd == "reset-all":
        limiter = RateLimiter()
        limiter.reset_all()
        print("All rate-limit counters cleared.")
