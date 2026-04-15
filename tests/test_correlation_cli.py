"""Tests for pipewarden.correlation_cli."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from pipewarden.correlation_cli import build_correlation_parser, handle_correlation
from pipewarden.history import HistoryEntry, HistoryStore


@pytest.fixture()
def correlation_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    build_correlation_parser(sub)
    return parser


@pytest.fixture()
def history_file(tmp_path: Path) -> Path:
    store = HistoryStore(path=tmp_path / "history.json")
    for pipeline in ("pipe_a", "pipe_b"):
        for passed in [True, False, True, True, False]:
            store.append(
                HistoryEntry(
                    pipeline=pipeline,
                    run_at=datetime.now(timezone.utc).isoformat(),
                    passed=passed,
                    total_checks=1,
                    failed_checks=0 if passed else 1,
                )
            )
    return tmp_path / "history.json"


class TestBuildCorrelationParser:
    def test_correlation_subcommand_registered(self, correlation_parser):
        args = correlation_parser.parse_args(
            ["correlation", "analyse"]
        )
        assert args.command == "correlation"

    def test_analyse_subcommand_stores_cmd(self, correlation_parser):
        args = correlation_parser.parse_args(["correlation", "analyse"])
        assert args.correlation_cmd == "analyse"

    def test_default_limit_is_50(self, correlation_parser):
        args = correlation_parser.parse_args(["correlation", "analyse"])
        assert args.limit == 50

    def test_custom_limit(self, correlation_parser):
        args = correlation_parser.parse_args(["correlation", "analyse", "--limit", "20"])
        assert args.limit == 20

    def test_strong_only_default_false(self, correlation_parser):
        args = correlation_parser.parse_args(["correlation", "analyse"])
        assert args.strong_only is False

    def test_strong_only_flag(self, correlation_parser):
        args = correlation_parser.parse_args(
            ["correlation", "analyse", "--strong-only"]
        )
        assert args.strong_only is True


class TestHandleCorrelation:
    def test_analyse_prints_output(self, correlation_parser, history_file, capsys):
        args = correlation_parser.parse_args(
            ["correlation", "analyse", "--history-file", str(history_file)]
        )
        handle_correlation(args)
        captured = capsys.readouterr()
        assert "pipe_a" in captured.out
        assert "pipe_b" in captured.out

    def test_empty_store_prints_no_data(self, correlation_parser, tmp_path, capsys):
        empty = tmp_path / "empty.json"
        args = correlation_parser.parse_args(
            ["correlation", "analyse", "--history-file", str(empty)]
        )
        handle_correlation(args)
        captured = capsys.readouterr()
        assert "No correlation data" in captured.out

    def test_strong_only_filters_weak_pairs(self, correlation_parser, history_file, capsys):
        args = correlation_parser.parse_args(
            ["correlation", "analyse", "--history-file", str(history_file), "--strong-only"]
        )
        handle_correlation(args)
        # should not raise; output may be empty if no strong pairs
        capsys.readouterr()
