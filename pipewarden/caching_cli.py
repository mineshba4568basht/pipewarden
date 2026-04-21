"""CLI sub-commands for result cache management."""
from __future__ import annotations

import argparse

from pipewarden.caching import CachePolicy, ResultCache


def build_caching_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("cache", help="Manage the result cache")
    sub = p.add_subparsers(dest="cache_cmd")

    info = sub.add_parser("info", help="Show cache policy and current size")
    info.add_argument("--ttl", type=int, default=300, help="TTL in seconds (default: 300)")
    info.add_argument("--max-entries", type=int, default=256, help="Max entries (default: 256)")

    clear = sub.add_parser("clear", help="Clear all cached results")
    clear.add_argument("--pipeline", default=None, help="Limit clear to a specific pipeline")
    clear.add_argument("--check", default=None, help="Limit clear to a specific check")

    p.set_defaults(func=handle_caching)
    return p


def handle_caching(args: argparse.Namespace, cache: ResultCache) -> None:
    cmd = getattr(args, "cache_cmd", None)
    if cmd == "info":
        _cmd_info(args, cache)
    elif cmd == "clear":
        _cmd_clear(args, cache)
    else:
        print("No cache sub-command specified. Use 'cache info' or 'cache clear'.")


def _cmd_info(args: argparse.Namespace, cache: ResultCache) -> None:
    policy = CachePolicy(ttl_seconds=args.ttl, max_entries=args.max_entries)
    print(str(policy))
    print(f"Current entries: {cache.size}")


def _cmd_clear(args: argparse.Namespace, cache: ResultCache) -> None:
    pipeline = getattr(args, "pipeline", None)
    check = getattr(args, "check", None)
    if pipeline and check:
        removed = cache.invalidate(pipeline, check)
        print(f"Invalidated {'1' if removed else '0'} entry for {pipeline}::{check}.")
    else:
        removed = cache.clear()
        print(f"Cleared {removed} cached result(s).")
