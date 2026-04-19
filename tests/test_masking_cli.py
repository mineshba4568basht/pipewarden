"""Tests for pipewarden.masking_cli."""
import argparse
import json
import pytest
from pipewarden.masking_cli import build_masking_parser, handle_masking


@pytest.fixture
def masking_parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_masking_parser(sub)
    return root


class TestBuildMaskingParser:
    def test_masking_subcommand_registered(self, masking_parser):
        args = masking_parser.parse_args(["masking", "info"])
        assert args.cmd == "masking"

    def test_info_subcommand_exists(self, masking_parser):
        args = masking_parser.parse_args(["masking", "info"])
        assert args.masking_cmd == "info"

    def test_info_default_pattern_none(self, masking_parser):
        args = masking_parser.parse_args(["masking", "info"])
        assert args.pattern is None

    def test_test_subcommand_exists(self, masking_parser):
        args = masking_parser.parse_args(["masking", "test", '{"password": "x"}'])
        assert args.masking_cmd == "test"

    def test_test_stores_data(self, masking_parser):
        args = masking_parser.parse_args(["masking", "test", '{"k": "v"}'])
        assert args.data == '{"k": "v"}'


class TestHandleMasking:
    def _args(self, masking_cmd, data=None, pattern=None):
        ns = argparse.Namespace(masking_cmd=masking_cmd, pattern=pattern, data=data)
        return ns

    def test_info_prints_policy(self, capsys):
        handle_masking(self._args("info"))
        out = capsys.readouterr().out
        assert "MaskingPolicy" in out

    def test_test_masks_sensitive(self, capsys):
        handle_masking(self._args("test", data='{"token": "abc", "rows": 10}'))
        out = capsys.readouterr().out
        assert "***" in out

    def test_test_invalid_json(self, capsys):
        handle_masking(self._args("test", data="not-json"))
        out = capsys.readouterr().out
        assert "error" in out

    def test_no_subcommand_fallback(self, capsys):
        handle_masking(self._args(None))
        out = capsys.readouterr().out
        assert "no subcommand" in out
