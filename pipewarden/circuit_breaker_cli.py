"""CLI commands for circuit breaker management."""
from __future__ import annotations
import argparse
from pipewarden.circuit_breaker import CircuitBreakerRegistry

_registry = CircuitBreakerRegistry()


def build_circuit_breaker_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("circuit-breaker", help="Manage circuit breakers")
    s = p.add_subparsers(dest="cb_cmd")

    lst = s.add_parser("list", help="List all circuit breakers")
    lst.set_defaults(cb_cmd="list")

    rst = s.add_parser("reset", help="Reset a circuit breaker")
    rst.add_argument("pipeline", help="Pipeline name")

    chk = s.add_parser("status", help="Check circuit breaker status")
    chk.add_argument("pipeline", help="Pipeline name")
    chk.add_argument("--threshold", type=int, default=5)
    chk.add_argument("--recovery-timeout", type=int, default=60)

    p.set_defaults(func=handle_circuit_breaker)


def handle_circuit_breaker(args: argparse.Namespace) -> None:
    cmd = getattr(args, "cb_cmd", None)
    if cmd == "list":
        _cmd_list()
    elif cmd == "reset":
        _cmd_reset(args)
    elif cmd == "status":
        _cmd_status(args)
    else:
        print("No circuit-breaker subcommand given. Use --help.")


def _cmd_list() -> None:
    breakers = _registry.all()
    if not breakers:
        print("No circuit breakers registered.")
        return
    for cb in breakers:
        print(cb)


def _cmd_reset(args: argparse.Namespace) -> None:
    if _registry.reset(args.pipeline):
        print(f"Circuit breaker for '{args.pipeline}' reset to CLOSED.")
    else:
        print(f"No circuit breaker found for '{args.pipeline}'.")


def _cmd_status(args: argparse.Namespace) -> None:
    cb = _registry.get(
        args.pipeline,
        failure_threshold=args.threshold,
        recovery_timeout=args.recovery_timeout,
    )
    print(cb)
    print(f"  allow_request={cb.allow_request()}")
