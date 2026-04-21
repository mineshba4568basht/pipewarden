"""CLI sub-commands for the redaction module."""
from __future__ import annotations

import argparse

from pipewarden.redaction import RedactionPolicy, _DEFAULT_PATTERNS


def build_redaction_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *redaction* sub-command group."""
    parser = subparsers.add_parser(
        "redaction",
        help="Inspect and test the redaction policy",
    )
    sub = parser.add_subparsers(dest="redaction_cmd")

    # info
    info = sub.add_parser("info", help="Show active redaction patterns")
    info.add_argument(
        "--pattern",
        default=None,
        help="Filter output to patterns matching this string",
    )

    # test
    test = sub.add_parser("test", help="Test whether a key would be redacted")
    test.add_argument("key", help="Metadata key to test")

    parser.set_defaults(handle=handle_redaction)


def handle_redaction(args: argparse.Namespace) -> None:
    """Dispatch redaction sub-commands."""
    policy = RedactionPolicy()

    if args.redaction_cmd == "info":
        _cmd_info(args, policy)
    elif args.redaction_cmd == "test":
        _cmd_test(args, policy)
    else:
        print("No redaction sub-command given. Use --help for usage.")


def _cmd_info(args: argparse.Namespace, policy: RedactionPolicy) -> None:
    patterns = policy.patterns
    if args.pattern:
        patterns = [p for p in patterns if args.pattern.lower() in p.lower()]
    print(f"Active redaction patterns ({len(patterns)}):")
    for p in patterns:
        print(f"  {p}")


def _cmd_test(args: argparse.Namespace, policy: RedactionPolicy) -> None:
    sensitive = policy.is_sensitive(args.key)
    verdict = "REDACTED" if sensitive else "allowed"
    print(f"Key '{args.key}' would be: {verdict}")
