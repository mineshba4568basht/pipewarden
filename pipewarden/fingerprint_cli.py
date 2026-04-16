"""CLI sub-commands for fingerprint inspection."""
from __future__ import annotations

import argparse

from pipewarden.fingerprint import FingerprintStore


def build_fingerprint_parser(subparsers: argparse._SubParsersAction) -> None:
    fp = subparsers.add_parser("fingerprint", help="Inspect alert fingerprints")
    sub = fp.add_subparsers(dest="fp_cmd")

    lst = sub.add_parser("list", help="List recorded fingerprints")
    lst.add_argument("--limit", type=int, default=20, help="Max rows to show")

    clr = sub.add_parser("clear", help="Clear all fingerprints")
    clr.set_defaults(fp_cmd="clear")


def handle_fingerprint(args: argparse.Namespace, store: FingerprintStore) -> None:
    if args.fp_cmd == "list":
        _cmd_list(args, store)
    elif args.fp_cmd == "clear":
        _cmd_clear(store)
    else:
        print("No fingerprint sub-command given. Use --help.")


def _cmd_list(args: argparse.Namespace, store: FingerprintStore) -> None:
    records = store.all()[: args.limit]
    if not records:
        print("No fingerprints recorded.")
        return
    for fp in records:
        print(fp)


def _cmd_clear(store: FingerprintStore) -> None:
    store.clear()
    print("Fingerprint store cleared.")
