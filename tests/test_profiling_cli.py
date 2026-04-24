"""Tests for pipewarden.profiling_cli."""
from __future__ import annotations

import argparse
import pytest
from pipewarden.profiling import ProfilingStore
from pipewarden.profiling_cli import build_profiling_parser, handle_profiling


@pytest.fixture()
def profiling_parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_profiling_parser(sub)
    return root


@pytest.fixture()
def populated_store():
    store = ProfilingStore()
    store.record("etl", "row_count", 30.0)
    store.record("etl", "row_count", 50.0)
    store.record("etl", "null_check", 15.0)
    return store


class TestBuildProfilingParser:
    def test_profile_subcommand_registered(self, profiling_parser):
        args = profiling_parser.parse_args(["profile", "list"])
        assert args.command == "profile"

    def test_list_default_limit(self, profiling_parser):
        args = profiling_parser.parse_args(["profile", "list"])
        assert args.limit == 20

    def test_list_custom_limit(self, profiling_parser):
        args = profiling_parser.parse_args(["profile", "list", "--limit", "5"])
        assert args.limit == 5

    def test_report_stores_pipeline_and_check(self, profiling_parser):
        args = profiling_parser.parse_args(["profile", "report", "etl", "row_count"])
        assert args.pipeline == "etl"
        assert args.check == "row_count"

    def test_clear_default_pipeline_none(self, profiling_parser):
        args = profiling_parser.parse_args(["profile", "clear"])
        assert args.pipeline is None

    def test_clear_with_pipeline(self, profiling_parser):
        args = profiling_parser.parse_args(["profile", "clear", "--pipeline", "etl"])
        assert args.pipeline == "etl"


class TestHandleProfiling:
    def test_list_prints_samples(self, profiling_parser, populated_store, capsys):
        args = profiling_parser.parse_args(["profile", "list"])
        handle_profiling(args, store=populated_store)
        out = capsys.readouterr().out
        assert "etl" in out

    def test_list_empty_store(self, profiling_parser, capsys):
        args = profiling_parser.parse_args(["profile", "list"])
        handle_profiling(args, store=ProfilingStore())
        out = capsys.readouterr().out
        assert "No profiling samples" in out

    def test_report_output(self, profiling_parser, populated_store, capsys):
        args = profiling_parser.parse_args(["profile", "report", "etl", "row_count"])
        handle_profiling(args, store=populated_store)
        out = capsys.readouterr().out
        assert "mean=" in out

    def test_clear_removes_samples(self, profiling_parser, populated_store, capsys):
        args = profiling_parser.parse_args(["profile", "clear"])
        handle_profiling(args, store=populated_store)
        out = capsys.readouterr().out
        assert "Removed" in out
        assert populated_store.all_samples() == []

    def test_no_subcommand_prints_help(self, profiling_parser, capsys):
        args = profiling_parser.parse_args(["profile"])
        handle_profiling(args, store=ProfilingStore())
        out = capsys.readouterr().out
        assert "help" in out.lower() or "subcommand" in out.lower()
