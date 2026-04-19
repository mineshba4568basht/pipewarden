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
    """Dispatch ratelimit sub-commands to the appropriate handler."""
    if args.ratelimit_cmd == "info":
        _handle_info(args)
    elif args.ratelimit_cmd == "reset":
        _handle_reset(args)
    elif args.ratelimit_cmd == "reset-all":
        _handle_reset_all()


def _handle_info(args: argparse.Namespace) -> None:
    """Display the effective rate-limit policy."""
    if args.max_alerts <= 0:
        raise ValueError("--max-alerts must be a positive integer")
    if args.window <= 0:
        raise ValueError("--window must be a positive integer")
    policy = RateLimitPolicy(
        max_alerts=args.max_alerts,
        window_seconds=args.window,
    )
    print(policy)


def _handle_reset(args: argparse.Namespace) -> None:
    """Reset rate-limit counters for a single pipeline."""
    limiter = RateLimiter()
    limiter.reset(args.pipeline)
    print(f"Rate-limit counters cleared for pipeline: {args.pipeline}")


def _handle_reset_all() -> None:
    """Reset rate-limit counters for all pipelines."""
    limiter = RateLimiter()
    limiter.reset_all()
    print("All rate-limit counters cleared.")
