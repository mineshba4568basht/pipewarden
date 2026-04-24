"""CLI commands for pipeline profiling."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewarden.profiling import ProfilingStore


def build_profiling_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = sub.add_parser("profile", help="Pipeline execution profiling")
    cmds = p.add_subparsers(dest="profile_cmd")

    lst = cmds.add_parser("list", help="List recent profiling samples")
    lst.add_argument("--limit", type=int, default=20, help="Max samples to show")

    rep = cmds.add_parser("report", help="Show stats for a pipeline/check pair")
    rep.add_argument("pipeline", help="Pipeline name")
    rep.add_argument("check", help="Check name")

    clr = cmds.add_parser("clear", help="Remove stored profiling samples")
    clr.add_argument("--pipeline", default=None, help="Limit to pipeline")

    return p


def _cmd_list(args: argparse.Namespace, store: ProfilingStore) -> None:
    samples = store.all_samples(limit=args.limit)
    if not samples:
        print("No profiling samples recorded.")
        return
    for s in samples:
        print(s)


def _cmd_report(args: argparse.Namespace, store: ProfilingStore) -> None:
    report = store.report(args.pipeline, args.check)
    print(report)


def _cmd_clear(args: argparse.Namespace, store: ProfilingStore) -> None:
    removed = store.clear(pipeline=getattr(args, "pipeline", None))
    print(f"Removed {removed} sample(s).")


def handle_profiling(args: argparse.Namespace, store: Optional[ProfilingStore] = None) -> None:
    if store is None:
        store = ProfilingStore()
    dispatch = {
        "list": _cmd_list,
        "report": _cmd_report,
        "clear": _cmd_clear,
    }
    cmd = getattr(args, "profile_cmd", None)
    if cmd in dispatch:
        dispatch[cmd](args, store)
    else:
        print("No profile subcommand given. Use --help.")
