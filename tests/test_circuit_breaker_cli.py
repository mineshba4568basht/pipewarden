"""Tests for pipewarden.circuit_breaker_cli."""
from __future__ import annotations
import argparse
from unittest.mock import patch, MagicMock
import pytest
from pipewarden.circuit_breaker_cli import build_circuit_breaker_parser, handle_circuit_breaker


@pytest.fixture()
def cb_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    build_circuit_breaker_parser(sub)
    return parser


class TestBuildCircuitBreakerParser:
    def test_subcommand_registered(self, cb_parser):
        args = cb_parser.parse_args(["circuit-breaker", "list"])
        assert args.command == "circuit-breaker"

    def test_list_subcommand(self, cb_parser):
        args = cb_parser.parse_args(["circuit-breaker", "list"])
        assert args.cb_cmd == "list"

    def test_reset_stores_pipeline(self, cb_parser):
        args = cb_parser.parse_args(["circuit-breaker", "reset", "my_pipe"])
        assert args.pipeline == "my_pipe"

    def test_status_default_threshold(self, cb_parser):
        args = cb_parser.parse_args(["circuit-breaker", "status", "p"])
        assert args.threshold == 5

    def test_status_default_recovery_timeout(self, cb_parser):
        args = cb_parser.parse_args(["circuit-breaker", "status", "p"])
        assert args.recovery_timeout == 60

    def test_status_custom_threshold(self, cb_parser):
        args = cb_parser.parse_args(["circuit-breaker", "status", "p", "--threshold", "3"])
        assert args.threshold == 3


class TestHandleCircuitBreaker:
    def test_list_no_breakers(self, cb_parser, capsys):
        args = cb_parser.parse_args(["circuit-breaker", "list"])
        import pipewarden.circuit_breaker_cli as mod
        mod._registry._breakers.clear()
        handle_circuit_breaker(args)
        out = capsys.readouterr().out
        assert "No circuit breakers" in out

    def test_reset_nonexistent(self, cb_parser, capsys):
        args = cb_parser.parse_args(["circuit-breaker", "reset", "ghost"])
        import pipewarden.circuit_breaker_cli as mod
        mod._registry._breakers.clear()
        handle_circuit_breaker(args)
        out = capsys.readouterr().out
        assert "No circuit breaker found" in out

    def test_status_prints_info(self, cb_parser, capsys):
        args = cb_parser.parse_args(["circuit-breaker", "status", "mypipe"])
        import pipewarden.circuit_breaker_cli as mod
        mod._registry._breakers.clear()
        handle_circuit_breaker(args)
        out = capsys.readouterr().out
        assert "mypipe" in out
        assert "allow_request" in out

    def test_no_cmd_prints_help(self, cb_parser, capsys):
        args = cb_parser.parse_args(["circuit-breaker"])
        handle_circuit_breaker(args)
        out = capsys.readouterr().out
        assert "--help" in out
