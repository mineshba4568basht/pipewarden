"""CLI sub-command for the transformation module."""
from __future__ import annotations

import argparse

from pipewarden.transformation import TransformationRule, transform


def build_transformation_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # noqa: SLF001
    p = sub.add_parser("transform", help="Apply a value transformation rule")
    sp = p.add_subparsers(dest="transform_cmd")

    # --- info sub-command ---
    info = sp.add_parser("info", help="Show available built-in transform functions")
    info.set_defaults(transform_cmd="info")

    # --- apply sub-command ---
    apply_p = sp.add_parser("apply", help="Apply a transformation to a value")
    apply_p.add_argument("--value", type=float, required=True, help="Input value")
    apply_p.add_argument(
        "--fn",
        default="abs",
        help="Transform function (default: abs)",
    )
    apply_p.add_argument(
        "--scale", type=float, default=1.0, help="Scale factor (default: 1.0)"
    )
    apply_p.add_argument(
        "--offset", type=float, default=0.0, help="Offset added before fn (default: 0.0)"
    )
    apply_p.add_argument(
        "--name", default="cli", help="Rule name label (default: cli)"
    )
    apply_p.set_defaults(transform_cmd="apply")

    p.set_defaults(func=handle_transformation)
    return p


def handle_transformation(args: argparse.Namespace) -> None:
    from pipewarden.transformation import _BUILT_IN_TRANSFORMS  # noqa: PLC0415

    cmd = getattr(args, "transform_cmd", None)

    if cmd == "info":
        print("Available transform functions:")
        for name in sorted(_BUILT_IN_TRANSFORMS):
            print(f"  {name}")
        return

    if cmd == "apply":
        try:
            rule = TransformationRule(
                name=args.name,
                fn=args.fn,
                scale=args.scale,
                offset=args.offset,
            )
        except ValueError as exc:
            print(f"Error: {exc}")
            return
        result = transform(rule, args.value)
        print(result)
        print(f"  Steps: {' -> '.join(result.steps)}")
        return

    print("No sub-command given. Use 'info' or 'apply'.")
