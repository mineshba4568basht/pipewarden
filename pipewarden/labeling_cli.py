"""CLI interface for labeling inspection."""
from __future__ import annotations
import argparse
from pipewarden.labeling import LabelRule, LabelSet


def build_labeling_parser(subparsers=None):
    if subparsers is None:
        parser = argparse.ArgumentParser(prog="pipewarden label")
        sub = parser.add_subparsers(dest="label_cmd")
    else:
        parser = subparsers.add_parser("label", help="Label management")
        sub = parser.add_subparsers(dest="label_cmd")

    info = sub.add_parser("info", help="Show label rule info")
    info.add_argument("--key", default=None)
    info.add_argument("--value", default=None)
    info.add_argument("--pipeline", default=None)
    info.add_argument("--severity", default=None)

    return parser


def handle_labeling(args: argparse.Namespace) -> None:
    cmd = getattr(args, "label_cmd", None)
    if cmd == "info":
        rule = LabelRule(
            key=args.key or "env",
            value=args.value or "production",
            pipeline=args.pipeline,
            severity=args.severity,
        )
        print(str(rule))
        ls = LabelSet()
        ls.add(rule.key, rule.value)
        print(str(ls))
    else:
        print("No label subcommand given. Use 'info'.")
