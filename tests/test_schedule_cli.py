"""Tests for pipewarden.schedule_cli."""

from __future__ import annotations

import argparse
import pytest

from pipewarden.schedule_cli import build_schedule_parser, handle_schedule


@pytest.fixture()
def schedule_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pipewarden")
    sub = root.add_subparsers(dest="command")
    build_schedule_parser(sub)
    return root


class TestBuildScheduleParser:
    def test_schedule_subcommand_registered(self, schedule_parser):
        args = schedule_parser.parse_args(["schedule", "check", "* * * * *"])
        assert args.command == "schedule"

    def test_check_subcommand_stores_expression(self, schedule_parser):
        args = schedule_parser.parse_args(["schedule", "check", "@daily"])
        assert args.expression == "@daily"
        assert args.schedule_cmd == "check"

    def test_check_subcommand_at_default_none(self, schedule_parser):
        args = schedule_parser.parse_args(["schedule", "check", "* * * * *"])
        assert args.at is None

    def test_check_subcommand_at_flag(self, schedule_parser):
        args = schedule_parser.parse_args(
            ["schedule", "check", "0 9 * * *", "--at", "2024-06-01T09:00:00"]
        )
        assert args.at == "2024-06-01T09:00:00"

    def test_validate_subcommand_registered(self, schedule_parser):
        args = schedule_parser.parse_args(["schedule", "validate", "*/5 * * * *"])
        assert args.schedule_cmd == "validate"
        assert args.expression == "*/5 * * * *"


class TestHandleScheduleCheck:
    def test_due_output(self, schedule_parser, capsys):
        args = schedule_parser.parse_args(
            ["schedule", "check", "* * * * *", "--at", "2024-01-15T10:30:00"]
        )
        handle_schedule(args)
        captured = capsys.readouterr()
        assert "DUE" in captured.out

    def test_not_due_output(self, schedule_parser, capsys):
        # 0 9 * * * fires only at 09:00; check at 10:30
        args = schedule_parser.parse_args(
            ["schedule", "check", "0 9 * * *", "--at", "2024-01-15T10:30:00"]
        )
        handle_schedule(args)
        captured = capsys.readouterr()
        assert "not due" in captured.out

    def test_invalid_expression_prints_error(self, schedule_parser, capsys):
        args = schedule_parser.parse_args(
            ["schedule", "check", "bad expr", "--at", "2024-01-15T10:30:00"]
        )
        handle_schedule(args)
        captured = capsys.readouterr()
        assert "[ERROR]" in captured.out


class TestHandleScheduleValidate:
    def test_valid_expression_ok(self, schedule_parser, capsys):
        args = schedule_parser.parse_args(["schedule", "validate", "@weekly"])
        handle_schedule(args)
        captured = capsys.readouterr()
        assert "[OK]" in captured.out

    def test_invalid_expression_invalid(self, schedule_parser, capsys):
        args = schedule_parser.parse_args(["schedule", "validate", "not valid at all"])
        handle_schedule(args)
        captured = capsys.readouterr()
        assert "[INVALID]" in captured.out
