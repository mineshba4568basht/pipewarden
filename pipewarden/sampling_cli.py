"""CLI interface for the sampling module."""
from __future__ import annotations

import argparse

from pipewarden.sampling import SamplingPolicy


def build_sampling_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("sampling", help="Configure and inspect alert sampling")
    sp = p.add_subparsers(dest="sampling_cmd", required=True)

    info = sp.add_parser("info", help="Show current sampling policy")
    info.add_argument("--rate", type=float, default=1.0, help="Sampling rate (0-1]")

    check = sp.add_parser("check", help="Check whether a rate value is valid")
    check.add_argument("rate", type=float, help="Rate to validate")

    p.set_defaults(func=handle_sampling)


def handle_sampling(args: argparse.Namespace) -> None:
    if args.sampling_cmd == "info":
        try:
            policy = SamplingPolicy(rate=args.rate)
            print(policy)
        except ValueError as exc:
            print(f"Error: {exc}")
    elif args.sampling_cmd == "check":
        try:
            policy = SamplingPolicy(rate=args.rate)
            print(f"Valid: {policy}")
        except ValueError as exc:
            print(f"Invalid rate {args.rate}: {exc}")
