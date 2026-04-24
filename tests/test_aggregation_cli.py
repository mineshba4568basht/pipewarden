"""Tests for pipewarden.aggregation_cli."""

from __future__ import annotations

import argparse

import pytest

from pipewarden.aggregation_cli import build_aggregation_parser


@pytest.fixture()
def agg_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pipewarden")
    sub = root.add_subparsers(dest="command")
    build_aggregation_parser(sub)
    return root


class TestBuildAggregationParser:
    def test_aggregation_subcommand_registered(self, agg_parser):
        args = agg_parser.parse_args(["aggregation", "info"])
        assert args.command == "aggregation"

    def test_info_default_window(self, agg_parser):
        args = agg_parser.parse_args(["aggregation", "info"])
        assert args.window == 60

    def test_info_default_max_events(self, agg_parser):
        args = agg_parser.parse_args(["aggregation", "info"])
        assert args.max_events == 100

    def test_info_default_group_by(self, agg_parser):
        args = agg_parser.parse_args(["aggregation", "info"])
        assert args.group_by == "pipeline"

    def test_info_custom_window(self, agg_parser):
        args = agg_parser.parse_args(["aggregation", "info", "--window", "120"])
        assert args.window == 120

    def test_info_custom_max_events(self, agg_parser):
        args = agg_parser.parse_args(["aggregation", "info", "--max-events", "50"])
        assert args.max_events == 50

    def test_info_group_by_check(self, agg_parser):
        args = agg_parser.parse_args(["aggregation", "info", "--group-by", "check"])
        assert args.group_by == "check"

    def test_info_group_by_severity(self, agg_parser):
        args = agg_parser.parse_args(["aggregation", "info", "--group-by", "severity"])
        assert args.group_by == "severity"

    def test_info_invalid_group_by_raises(self, agg_parser):
        with pytest.raises(SystemExit):
            agg_parser.parse_args(["aggregation", "info", "--group-by", "unknown"])

    def test_func_is_set(self, agg_parser):
        from pipewarden.aggregation_cli import handle_aggregation
        args = agg_parser.parse_args(["aggregation", "info"])
        assert args.func is handle_aggregation
