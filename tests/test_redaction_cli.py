"""Tests for pipewarden.redaction_cli."""
from __future__ import annotations

import argparse
import pytest

from pipewarden.redaction_cli import build_redaction_parser, handle_redaction


@pytest.fixture()
def redaction_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pipewarden")
    sub = root.add_subparsers(dest="command")
    build_redaction_parser(sub)
    return root


class TestBuildRedactionParser:
    def test_redaction_subcommand_registered(self, redaction_parser):
        args = redaction_parser.parse_args(["redaction", "info"])
        assert args.command == "redaction"

    def test_info_subcommand_exists(self, redaction_parser):
        args = redaction_parser.parse_args(["redaction", "info"])
        assert args.redaction_cmd == "info"

    def test_info_default_pattern_none(self, redaction_parser):
        args = redaction_parser.parse_args(["redaction", "info"])
        assert args.pattern is None

    def test_info_pattern_flag(self, redaction_parser):
        args = redaction_parser.parse_args(["redaction", "info", "--pattern", "token"])
        assert args.pattern == "token"

    def test_test_subcommand_exists(self, redaction_parser):
        args = redaction_parser.parse_args(["redaction", "test", "my_key"])
        assert args.redaction_cmd == "test"

    def test_test_subcommand_stores_key(self, redaction_parser):
        args = redaction_parser.parse_args(["redaction", "test", "api_key"])
        assert args.key == "api_key"

    def test_handle_registered(self, redaction_parser):
        args = redaction_parser.parse_args(["redaction", "info"])
        assert callable(args.handle)


class TestHandleRedaction:
    def test_info_prints_patterns(self, redaction_parser, capsys):
        args = redaction_parser.parse_args(["redaction", "info"])
        handle_redaction(args)
        out = capsys.readouterr().out
        assert "password" in out
        assert "token" in out

    def test_info_filter_by_pattern(self, redaction_parser, capsys):
        args = redaction_parser.parse_args(["redaction", "info", "--pattern", "password"])
        handle_redaction(args)
        out = capsys.readouterr().out
        assert "password" in out
        # unrelated patterns should be absent
        assert "secret" not in out

    def test_test_sensitive_key(self, redaction_parser, capsys):
        args = redaction_parser.parse_args(["redaction", "test", "password"])
        handle_redaction(args)
        out = capsys.readouterr().out
        assert "REDACTED" in out

    def test_test_non_sensitive_key(self, redaction_parser, capsys):
        args = redaction_parser.parse_args(["redaction", "test", "row_count"])
        handle_redaction(args)
        out = capsys.readouterr().out
        assert "allowed" in out

    def test_no_subcommand_prints_help_hint(self, redaction_parser, capsys):
        args = redaction_parser.parse_args(["redaction"])
        args.redaction_cmd = None
        handle_redaction(args)
        out = capsys.readouterr().out
        assert "--help" in out
