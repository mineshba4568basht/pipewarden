"""CLI helpers for the masking feature."""
from __future__ import annotations
import argparse
import json
from pipewarden.masking import MaskingPolicy, mask_event_metadata


def build_masking_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser("masking", help="Inspect or test field masking policy")
    sp = p.add_subparsers(dest="masking_cmd")

    info = sp.add_parser("info", help="Show active masking patterns")
    info.add_argument("--pattern", nargs="*", default=None, help="Custom patterns")

    test = sp.add_parser("test", help="Test masking against a JSON dict")
    test.add_argument("data", help="JSON string of key/value pairs to mask")
    test.add_argument("--pattern", nargs="*", default=None)

    p.set_defaults(func=handle_masking)
    return p


def handle_masking(args: argparse.Namespace) -> None:
    patterns = args.pattern or None
    policy = MaskingPolicy(patterns=patterns) if patterns else MaskingPolicy()

    if args.masking_cmd == "info":
        print(str(policy))
        return

    if args.masking_cmd == "test":
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError as exc:
            print(f"[error] invalid JSON: {exc}")
            return
        result = mask_event_metadata(data, policy)
        print(str(result))
        for k, v in result.data.items():
            print(f"  {k}: {v}")
        return

    print("[masking] no subcommand given — try 'info' or 'test'")
