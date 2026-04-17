"""Tests for pipewarden.ratelimit_cli."""
from __future__ import annotations
import argparse
import pytest

from pipewarden.ratelimit_cli import build_ratelimit_parser, handle_ratelimit


@pytest.fixture()
def ratelimit_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    build_ratelimit_parser(sub)
    return parser


class TestBuildRateLimitParser:
    def test_ratelimit_subcommand_registered(self, ratelimit_parser):
        args = ratelimit_parser.parse_args(["ratelimit", "info"])
        assert args.command == "ratelimit"

    def test_info_default_max_alerts(self, ratelimit_parser):
        args = ratelimit_parser.parse_args(["ratelimit", "info"])
        assert args.max_alerts == 5

    def test_info_default_window(self, ratelimit_parser):
        args = ratelimit_parser.parse_args(["ratelimit", "info"])
        assert args.window == 300

    def test_info_custom_values(self, ratelimit_parser):
        args = ratelimit_parser.parse_args(
            ["ratelimit", "info", "--max-alerts", "10", "--window", "600"]
        )
        assert args.max_alerts == 10
        assert args.window == 600

    def test_reset_stores_pipeline(self, ratelimit_parser):
        args = ratelimit_parser.parse_args(["ratelimit", "reset", "my_pipe"])
        assert args.pipeline == "my_pipe"

    def test_reset_all_subcommand(self, ratelimit_parser):
        args = ratelimit_parser.parse_args(["ratelimit", "reset-all"])
        assert args.ratelimit_cmd == "reset-all"


class TestHandleRateLimit:
    def test_info_prints_policy(self, ratelimit_parser, capsys):
        args = ratelimit_parser.parse_args(["ratelimit", "info", "--max-alerts", "3"])
        handle_ratelimit(args)
        out = capsys.readouterr().out
        assert "3" in out

    def test_reset_prints_confirmation(self, ratelimit_parser, capsys):
        args = ratelimit_parser.parse_args(["ratelimit", "reset", "pipe_x"])
        handle_ratelimit(args)
        out = capsys.readouterr().out
        assert "pipe_x" in out

    def test_reset_all_prints_confirmation(self, ratelimit_parser, capsys):
        args = ratelimit_parser.parse_args(["ratelimit", "reset-all"])
        handle_ratelimit(args)
        out = capsys.readouterr().out
        assert "cleared" in out.lower()
