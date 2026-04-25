"""Tests for pipewarden.tracing_cli."""
from __future__ import annotations

import argparse
from io import StringIO
from unittest.mock import patch

import pytest

from pipewarden.tracing_cli import build_tracing_parser, handle_tracing


@pytest.fixture
def tracing_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pipewarden")
    sub = root.add_subparsers(dest="command")
    build_tracing_parser(sub)
    return root


class TestBuildTracingParser:
    def test_tracing_subcommand_registered(self, tracing_parser):
        args = tracing_parser.parse_args(["tracing", "demo"])
        assert args.command == "tracing"

    def test_demo_subcommand_stores_cmd(self, tracing_parser):
        args = tracing_parser.parse_args(["tracing", "demo"])
        assert args.tracing_cmd == "demo"

    def test_demo_default_pipelines(self, tracing_parser):
        args = tracing_parser.parse_args(["tracing", "demo"])
        assert "orders" in args.pipelines
        assert "inventory" in args.pipelines

    def test_demo_custom_pipelines(self, tracing_parser):
        args = tracing_parser.parse_args(["tracing", "demo", "--pipelines", "sales", "returns"])
        assert args.pipelines == ["sales", "returns"]

    def test_demo_default_fail_check_is_none(self, tracing_parser):
        args = tracing_parser.parse_args(["tracing", "demo"])
        assert args.fail_check is None

    def test_demo_fail_check_stored(self, tracing_parser):
        args = tracing_parser.parse_args(["tracing", "demo", "--fail", "null_check"])
        assert args.fail_check == "null_check"


class TestHandleTracing:
    def _run(self, argv: list, tracing_parser: argparse.ArgumentParser) -> str:
        args = tracing_parser.parse_args(argv)
        buf = StringIO()
        with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
            handle_tracing(args)
        return buf.getvalue()

    def test_demo_prints_trace_id(self, tracing_parser):
        out = self._run(["tracing", "demo"], tracing_parser)
        assert "Starting trace:" in out

    def test_demo_prints_all_passed(self, tracing_parser):
        out = self._run(["tracing", "demo"], tracing_parser)
        assert "All spans passed" in out

    def test_demo_with_fail_reports_failed_spans(self, tracing_parser):
        out = self._run(["tracing", "demo", "--fail", "null_check"], tracing_parser)
        assert "failed" in out.lower()

    def test_no_subcommand_prints_help_hint(self, tracing_parser):
        args = tracing_parser.parse_args(["tracing"])
        buf = StringIO()
        with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
            handle_tracing(args)
        assert "--help" in buf.getvalue()
