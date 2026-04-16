"""CLI sub-commands for the audit log."""
from __future__ import annotations

import argparse

from pipewarden.audit import AuditLog


def build_audit_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    audit_p = subparsers.add_parser("audit", help="View and manage the audit log")
    sub = audit_p.add_subparsers(dest="audit_cmd", required=True)

    list_p = sub.add_parser("list", help="List recent audit entries")
    list_p.add_argument("--pipeline", default=None, help="Filter by pipeline name")
    list_p.add_argument("--limit", type=int, default=20, help="Max entries to show")
    list_p.add_argument("--audit-file", default=".pipewarden_audit.json")

    clear_p = sub.add_parser("clear", help="Clear all audit entries")
    clear_p.add_argument("--audit-file", default=".pipewarden_audit.json")

    return audit_p


def _cmd_list(args: argparse.Namespace) -> None:
    log = AuditLog(args.audit_file)
    entries = log.entries(pipeline=args.pipeline, limit=args.limit)
    if not entries:
        print("No audit entries found.")
        return
    for e in entries:
        print(e)


def _cmd_clear(args: argparse.Namespace) -> None:
    log = AuditLog(args.audit_file)
    removed = log.clear()
    print(f"Cleared {removed} audit entries.")


def handle_audit(args: argparse.Namespace) -> None:
    dispatch = {"list": _cmd_list, "clear": _cmd_clear}
    dispatch[args.audit_cmd](args)
