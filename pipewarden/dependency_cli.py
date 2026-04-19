"""CLI commands for dependency graph inspection."""
from __future__ import annotations
import argparse
from pipewarden.dependency import DependencyGraph, check_dependencies


def build_dependency_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("dependency", help="Pipeline dependency tools")
    sub = p.add_subparsers(dest="dep_cmd", required=True)

    lst = sub.add_parser("list", help="List edges")
    lst.add_argument("--upstream", default=None)

    chk = sub.add_parser("check", help="Check if pipeline is blocked")
    chk.add_argument("pipeline")
    chk.add_argument("--failed", nargs="*", default=[], metavar="PIPELINE")

    sub.add_parser("cycle", help="Detect cycles in the graph")
    p.set_defaults(func=handle_dependency)


def handle_dependency(args: argparse.Namespace) -> None:
    graph = DependencyGraph()
    # In a real integration the graph would be loaded from config/store.
    if args.dep_cmd == "list":
        _cmd_list(args, graph)
    elif args.dep_cmd == "check":
        _cmd_check(args, graph)
    elif args.dep_cmd == "cycle":
        _cmd_cycle(graph)


def _cmd_list(args: argparse.Namespace, graph: DependencyGraph) -> None:
    edges = graph.edges
    if args.upstream:
        edges = [e for e in edges if e.upstream == args.upstream]
    if not edges:
        print("No edges found.")
        return
    for e in edges:
        print(e)


def _cmd_check(args: argparse.Namespace, graph: DependencyGraph) -> None:
    result = check_dependencies(args.pipeline, graph, args.failed)
    print(result)


def _cmd_cycle(graph: DependencyGraph) -> None:
    if graph.has_cycle():
        print("CYCLE DETECTED in dependency graph.")
    else:
        print("No cycles detected.")
