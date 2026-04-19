"""Tests for pipewarden.priority_cli."""
from __future__ import annotations
import argparse
import pytest
from pipewarden.priority_cli import build_priority_parser, handle_priority


@pytest.fixture()
def priority_parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_priority_parser(sub)
    return root


class TestBuildPriorityParser:
    def test_priority_subcommand_registered(self, priority_parser):
        args = priority_parser.parse_args(["priority", "info"])
        assert args.command == "priority"

    def test_info_default_tag_bonus(self, priority_parser):
        args = priority_parser.parse_args(["priority", "info"])
        assert args.tag_bonus == 20

    def test_info_default_recurrence_weight(self, priority_parser):
        args = priority_parser.parse_args(["priority", "info"])
        assert args.recurrence_weight == 5

    def test_info_default_max_recurrence_bonus(self, priority_parser):
        args = priority_parser.parse_args(["priority", "info"])
        assert args.max_recurrence_bonus == 50

    def test_info_default_high_priority_tags_empty(self, priority_parser):
        args = priority_parser.parse_args(["priority", "info"])
        assert args.high_priority_tags == []

    def test_info_custom_tag_bonus(self, priority_parser):
        args = priority_parser.parse_args(["priority", "info", "--tag-bonus", "30"])
        assert args.tag_bonus == 30

    def test_info_custom_high_priority_tags(self, priority_parser):
        args = priority_parser.parse_args(["priority", "info", "--high-priority-tags", "tier1", "tier2"])
        assert args.high_priority_tags == ["tier1", "tier2"]


class TestHandlePriority:
    def test_info_prints_policy(self, priority_parser, capsys):
        args = priority_parser.parse_args(["priority", "info"])
        handle_priority(args)
        out = capsys.readouterr().out
        assert "PriorityPolicy" in out
        assert "tag_bonus" in out

    def test_no_subcommand_prints_help(self, priority_parser, capsys):
        args = priority_parser.parse_args(["priority"])
        args.priority_cmd = None
        handle_priority(args)
        out = capsys.readouterr().out
        assert "priority info" in out
