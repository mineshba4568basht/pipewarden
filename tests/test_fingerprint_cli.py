"""Tests for pipewarden.fingerprint_cli."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from pipewarden.fingerprint import FingerprintStore
from pipewarden.fingerprint_cli import build_fingerprint_parser, handle_fingerprint


@pytest.fixture()
def fp_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    build_fingerprint_parser(sub)
    return parser


@pytest.fixture()
def populated_store():
    store = FingerprintStore()
    event = MagicMock()
    event.rule.pipeline = "pipe_a"
    event.rule.severity = "warning"
    event.result.check_name = "row_count"
    store.record(event)
    return store


class TestBuildFingerprintParser:
    def test_fingerprint_subcommand_registered(self, fp_parser):
        args = fp_parser.parse_args(["fingerprint", "list"])
        assert args.command == "fingerprint"

    def test_list_default_limit(self, fp_parser):
        args = fp_parser.parse_args(["fingerprint", "list"])
        assert args.limit == 20

    def test_list_custom_limit(self, fp_parser):
        args = fp_parser.parse_args(["fingerprint", "list", "--limit", "5"])
        assert args.limit == 5

    def test_clear_subcommand_stores_cmd(self, fp_parser):
        args = fp_parser.parse_args(["fingerprint", "clear"])
        assert args.fp_cmd == "clear"


class TestHandleFingerprint:
    def test_list_prints_entries(self, populated_store, capsys):
        args = argparse.Namespace(fp_cmd="list", limit=10)
        handle_fingerprint(args, populated_store)
        out = capsys.readouterr().out
        assert "pipe_a" in out

    def test_list_empty_store(self, capsys):
        args = argparse.Namespace(fp_cmd="list", limit=10)
        handle_fingerprint(args, FingerprintStore(), )
        out = capsys.readouterr().out
        assert "No fingerprints" in out

    def test_clear_empties_store(self, populated_store, capsys):
        args = argparse.Namespace(fp_cmd="clear")
        handle_fingerprint(args, populated_store)
        assert populated_store.all() == []

    def test_clear_prints_confirmation(self, populated_store, capsys):
        args = argparse.Namespace(fp_cmd="clear")
        handle_fingerprint(args, populated_store)
        out = capsys.readouterr().out
        assert "cleared" in out

    def test_no_cmd_prints_help_hint(self, capsys):
        args = argparse.Namespace(fp_cmd=None)
        handle_fingerprint(args, FingerprintStore())
        out = capsys.readouterr().out
        assert "--help" in out
