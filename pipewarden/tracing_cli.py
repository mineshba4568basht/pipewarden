"""CLI sub-commands for tracing inspection."""
from __future__ import annotations

import argparse
from typing import List

from pipewarden.tracing import TraceContext, TraceSpan, new_trace


def build_tracing_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("tracing", help="Inspect distributed trace spans")
    sub = parser.add_subparsers(dest="tracing_cmd")

    demo = sub.add_parser("demo", help="Run a demo trace and print spans")
    demo.add_argument(
        "--pipelines",
        nargs="+",
        default=["orders", "inventory"],
        metavar="PIPELINE",
        help="Pipeline names to include in demo trace",
    )
    demo.add_argument(
        "--fail",
        dest="fail_check",
        default=None,
        metavar="CHECK",
        help="Mark this check name as failed in the demo",
    )

    return parser


def _print_spans(spans: List[TraceSpan]) -> None:
    for span in spans:
        indent = "  " if span.parent_span_id else ""
        print(f"{indent}{span}")


def handle_tracing(args: argparse.Namespace) -> None:
    if args.tracing_cmd == "demo":
        ctx = new_trace()
        print(f"Starting trace: {ctx.trace_id}")
        root = ctx.start_span(pipeline=args.pipelines[0], check="root", tags={"env": "demo"})
        for pipeline in args.pipelines:
            for check in ("row_count", "null_check"):
                span = ctx.start_span(
                    pipeline=pipeline,
                    check=check,
                    parent_span_id=root.span_id,
                )
                status = "error" if args.fail_check and check == args.fail_check else "ok"
                span.finish(status=status)
        root.finish("error" if ctx.failed_spans() else "ok")
        print(ctx)
        _print_spans(ctx.spans)
        failed = ctx.failed_spans()
        if failed:
            print(f"\n{len(failed)} span(s) failed.")
        else:
            print("\nAll spans passed.")
    else:
        print("No tracing sub-command given. Use --help for options.")
