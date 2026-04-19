"""Tests for pipewarden.quota_cli."""
from __future__ import annotations

import argparse

import pytest

from pipewarden.quota_cli import build_quota_parser, handle_quota


@pytest.fixture()
def quota_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    build_quota_parser(sub)
    return parser


class TestBuildQuotaParser:
    def test_quota_subcommand_registered(self, quota_parser):
        args = quota_parser.parse_args(["quota", "info"])
        assert args.command == "quota"

    def test_info_default_max_alerts(self, quota_parser):
        args = quota_parser.parse_args(["quota", "info"])
        assert args.max_alerts == 10

    def test_info_default_window(self, quota_parser):
        args = quota_parser.parse_args(["quota", "info"])
        assert args.window_minutes == 60

    def test_info_custom_max_alerts(self, quota_parser):
        args = quota_parser.parse_args(["quota", "info", "--max-alerts", "5"])
        assert args.max_alerts == 5

    def test_info_custom_window(self, quota_parser):
        args = quota_parser.parse_args(["quota", "info", "--window", "30"])
        assert args.window_minutes == 30

    def test_reset_stores_pipeline(self, quota_parser):
        args = quota_parser.parse_args(["quota", "reset", "my_pipe"])
        assert args.pipeline == "my_pipe"


class TestHandleQuota:
    def test_info_prints_policy(self, quota_parser, capsys):
        args = quota_parser.parse_args(["quota", "info", "--max-alerts", "7"])
        handle_quota(args)
        out = capsys.readouterr().out
        assert "7" in out

    def test_reset_prints_confirmation(self, quota_parser, capsys):
        args = quota_parser.parse_args(["quota", "reset", "pipe_x"])
        handle_quota(args)
        out = capsys.readouterr().out
        assert "pipe_x" in out
