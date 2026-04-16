"""Tests for pipewarden.throttle_cli."""
from __future__ import annotations
import argparse
from datetime import datetime
from unittest.mock import patch
import pytest
from pipewarden.throttle import ThrottleManager, ThrottlePolicy, ThrottleRecord
from pipewarden.throttle_cli import build_throttle_parser, handle_throttle

T0 = datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def throttle_parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    build_throttle_parser(sub)
    return p


@pytest.fixture
def populated_manager():
    m = ThrottleManager(policy=ThrottlePolicy(cooldown_minutes=30))
    m.record("pipe_a", "row_count", now=T0)
    m.record("pipe_b", "null_check", now=T0)
    return m


class TestBuildThrottleParser:
    def test_throttle_subcommand_registered(self, throttle_parser):
        args = throttle_parser.parse_args(["throttle", "list"])
        assert args.throttle_cmd == "list"

    def test_clear_stores_pipeline_and_check(self, throttle_parser):
        args = throttle_parser.parse_args(["throttle", "clear", "my_pipe", "my_check"])
        assert args.pipeline == "my_pipe"
        assert args.check == "my_check"

    def test_info_default_cooldown(self, throttle_parser):
        args = throttle_parser.parse_args(["throttle", "info"])
        assert args.cooldown == 30

    def test_info_custom_cooldown(self, throttle_parser):
        args = throttle_parser.parse_args(["throttle", "info", "--cooldown", "60"])
        assert args.cooldown == 60


class TestHandleThrottle:
    def test_list_empty(self, throttle_parser, capsys):
        args = throttle_parser.parse_args(["throttle", "list"])
        handle_throttle(args, manager=ThrottleManager())
        out = capsys.readouterr().out
        assert "No active" in out

    def test_list_shows_records(self, throttle_parser, populated_manager, capsys):
        args = throttle_parser.parse_args(["throttle", "list"])
        handle_throttle(args, manager=populated_manager)
        out = capsys.readouterr().out
        assert "pipe_a" in out
        assert "pipe_b" in out

    def test_clear_removes_record(self, throttle_parser, populated_manager, capsys):
        args = throttle_parser.parse_args(["throttle", "clear", "pipe_a", "row_count"])
        handle_throttle(args, manager=populated_manager)
        assert len(populated_manager.active_records()) == 1
        out = capsys.readouterr().out
        assert "Cleared" in out

    def test_info_prints_policy(self, throttle_parser, capsys):
        args = throttle_parser.parse_args(["throttle", "info", "--cooldown", "15"])
        handle_throttle(args)
        out = capsys.readouterr().out
        assert "15" in out
