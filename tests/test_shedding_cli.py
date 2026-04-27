"""Tests for pipewarden.shedding_cli."""
from __future__ import annotations

import argparse
import pytest

from pipewarden.shedding_cli import build_shedding_parser, handle_shedding


@pytest.fixture()
def shedding_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pipewarden")
    sub = root.add_subparsers(dest="command")
    build_shedding_parser(sub)
    return root


class TestBuildSheddingParser:
    def test_shedding_subcommand_registered(self, shedding_parser):
        args = shedding_parser.parse_args(["shedding", "info"])
        assert args.command == "shedding"

    def test_info_default_max_queue_depth(self, shedding_parser):
        args = shedding_parser.parse_args(["shedding", "info"])
        assert args.max_queue_depth == 100

    def test_info_default_min_priority(self, shedding_parser):
        args = shedding_parser.parse_args(["shedding", "info"])
        assert args.min_priority == 0

    def test_info_default_shed_on_overload_true(self, shedding_parser):
        args = shedding_parser.parse_args(["shedding", "info"])
        assert args.shed_on_overload is True

    def test_info_no_shed_on_overload_flag(self, shedding_parser):
        args = shedding_parser.parse_args(["shedding", "info", "--no-shed-on-overload"])
        assert args.shed_on_overload is False

    def test_info_custom_max_queue_depth(self, shedding_parser):
        args = shedding_parser.parse_args(["shedding", "info", "--max-queue-depth", "50"])
        assert args.max_queue_depth == 50

    def test_info_custom_min_priority(self, shedding_parser):
        args = shedding_parser.parse_args(["shedding", "info", "--min-priority", "7"])
        assert args.min_priority == 7


class TestHandleShedding:
    def test_info_prints_policy(self, shedding_parser, capsys):
        args = shedding_parser.parse_args(["shedding", "info"])
        handle_shedding(args)
        out = capsys.readouterr().out
        assert "SheddingPolicy" in out

    def test_no_subcommand_prints_hint(self, capsys):
        args = argparse.Namespace(shedding_cmd=None)
        handle_shedding(args)
        out = capsys.readouterr().out
        assert "shedding info" in out
