"""CLI sub-commands for the validation module."""
from __future__ import annotations

import argparse
import json

from pipewarden.validation import ValidationRule, validate


def build_validation_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("validation", help="Validate pipeline records against rules.")
    sub = p.add_subparsers(dest="validation_cmd")

    # validate sub-command
    v = sub.add_parser("run", help="Validate a JSON record against inline rules.")
    v.add_argument("--pipeline", default="default", help="Pipeline name.")
    v.add_argument("--record", required=True, help="JSON string representing the record to validate.")
    v.add_argument(
        "--rule",
        dest="rules",
        action="append",
        default=[],
        metavar="FIELD:RULE[:VALUE]",
        help="Rule in the form field:rule or field:rule:value. May be repeated.",
    )

    # info sub-command
    sub.add_parser("info", help="Show available validation rule types.")

    p.set_defaults(func=handle_validation)
    return p


def _parse_rule(spec: str) -> ValidationRule:
    parts = spec.split(":", 2)
    if len(parts) < 2:
        raise argparse.ArgumentTypeError(f"Invalid rule spec {spec!r}. Expected FIELD:RULE[:VALUE].")
    field, rule = parts[0], parts[1]
    value: object = parts[2] if len(parts) == 3 else None
    # attempt numeric coercion for min/max
    if value is not None and rule in ("min", "max"):
        try:
            value = float(value)
        except ValueError:
            pass
    return ValidationRule(field=field, rule=rule, value=value)


def handle_validation(args: argparse.Namespace) -> None:
    cmd = getattr(args, "validation_cmd", None)

    if cmd == "run":
        try:
            record = json.loads(args.record)
        except json.JSONDecodeError as exc:
            print(f"[validation] Invalid JSON record: {exc}")
            return

        rules = []
        for spec in args.rules:
            try:
                rules.append(_parse_rule(spec))
            except (argparse.ArgumentTypeError, ValueError) as exc:
                print(f"[validation] Skipping bad rule {spec!r}: {exc}")

        result = validate(pipeline=args.pipeline, record=record, rules=rules)
        print(result)
        for v in result.violations:
            print(f"  {v}")
        if result.passed:
            print("  All rules passed.")

    elif cmd == "info":
        print("Available validation rules:")
        for r in ("required", "min", "max", "type", "regex"):
            print(f"  {r}")

    else:
        print("[validation] No sub-command given. Use 'run' or 'info'.")
