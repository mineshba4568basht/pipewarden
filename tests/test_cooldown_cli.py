"""Tests for pipewarden.cooldown_cli."""
from __future__ import annotations
import argparse
import pytest
from datetime import datetime
from pipewarden.cooldown import CooldownManager
from pipewarden.cooldown_cli import build_cooldown_parser, handle_cooldown


@pytest.fixture()
def cooldown_parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_cooldown_parser(sub)
    return p


@pytest.fixture()
def manager():
    m = CooldownManager(300)
    m.record("pipe", "check", now=datetime(2024, 1, 1))
    return m


class TestBuildCooldownParser:
    def test_cooldown_subcommand_registered(self, cooldown_parser):
        args = cooldown_parser.parse_args(["cooldown", "list"])
        assert args.command == "cooldown"

    def test_list_subcommand(self, cooldown_parser):
        args = cooldown_parser.parse_args(["cooldown", "list"])
        assert args.cooldown_cmd == "list"

    def test_clear_requires_pipeline_and_check(self, cooldown_parser):
        with pytest.raises(SystemExit):
            cooldown_parser.parse_args(["cooldown", "clear", "--pipeline", "p"])

    def test_clear_stores_pipeline_and_check(self, cooldown_parser):
        args = cooldown_parser.parse_args(
            ["cooldown", "clear", "--pipeline", "p", "--check", "c"]
        )
        assert args.pipeline == "p"
        assert args.check == "c"


class TestHandleCooldown:
    def test_list_prints_entries(self, manager, capsys):
        args = argparse.Namespace(cooldown_cmd="list")
        handle_cooldown(args, manager)
        out = capsys.readouterr().out
        assert "pipe" in out

    def test_list_empty(self, capsys):
        m = CooldownManager()
        args = argparse.Namespace(cooldown_cmd="list")
        handle_cooldown(args, m)
        out = capsys.readouterr().out
        assert "No active" in out

    def test_clear_existing(self, manager, capsys):
        args = argparse.Namespace(cooldown_cmd="clear", pipeline="pipe", check="check")
        handle_cooldown(args, manager)
        out = capsys.readouterr().out
        assert "Cleared" in out

    def test_clear_missing(self, capsys):
        m = CooldownManager()
        args = argparse.Namespace(cooldown_cmd="clear", pipeline="x", check="y")
        handle_cooldown(args, m)
        out = capsys.readouterr().out
        assert "No cooldown" in out
