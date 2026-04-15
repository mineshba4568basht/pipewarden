"""Tests for pipewarden.history_cli sub-commands."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from pipewarden.history import HistoryEntry, HistoryStore
from pipewarden.history_cli import build_history_parser, handle_history


@pytest.fixture()
def history_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    build_history_parser(sub)
    return parser


@pytest.fixture()
def populated_store(tmp_path: Path) -> Path:
    hist_file = tmp_path / "history.json"
    store = HistoryStore(path=hist_file)
    for i in range(3):
        store.append(
            HistoryEntry(
                run_id=f"run-{i}",
                timestamp=f"2024-01-0{i+1}T00:00:00",
                config_path="cfg.yaml",
                passed=i % 2 == 0,
                total_checks=3,
                failed_checks=0 if i % 2 == 0 else 1,
                alert_count=0,
            )
        )
    return hist_file


class TestBuildHistoryParser:
    def test_list_subcommand_registered(self, history_parser) -> None:
        args = history_parser.parse_args(["history", "list"])
        assert args.history_cmd == "list"

    def test_list_default_limit(self, history_parser) -> None:
        args = history_parser.parse_args(["history", "list"])
        assert args.limit == 10

    def test_list_custom_limit(self, history_parser) -> None:
        args = history_parser.parse_args(["history", "list", "-n", "5"])
        assert args.limit == 5

    def test_clear_subcommand_registered(self, history_parser) -> None:
        args = history_parser.parse_args(["history", "clear"])
        assert args.history_cmd == "clear"


class TestHandleHistory:
    def test_list_prints_entries(self, history_parser, populated_store, capsys) -> None:
        args = history_parser.parse_args(
            ["history", "list", "--history-file", str(populated_store)]
        )
        code = handle_history(args)
        assert code == 0
        captured = capsys.readouterr()
        assert "run-2" in captured.out

    def test_list_empty_store(self, history_parser, tmp_path, capsys) -> None:
        hist_file = tmp_path / "empty.json"
        args = history_parser.parse_args(
            ["history", "list", "--history-file", str(hist_file)]
        )
        code = handle_history(args)
        assert code == 0
        assert "No run history" in capsys.readouterr().out

    def test_list_respects_limit(self, history_parser, populated_store, capsys) -> None:
        args = history_parser.parse_args(
            ["history", "list", "-n", "1", "--history-file", str(populated_store)]
        )
        handle_history(args)
        lines = [l for l in capsys.readouterr().out.strip().splitlines() if l]
        assert len(lines) == 1

    def test_clear_removes_history(self, history_parser, populated_store, capsys) -> None:
        args = history_parser.parse_args(
            ["history", "clear", "--history-file", str(populated_store)]
        )
        code = handle_history(args)
        assert code == 0
        assert not populated_store.exists()
        assert "cleared" in capsys.readouterr().out.lower()

    def test_no_subcommand_returns_error(self, history_parser, capsys) -> None:
        args = history_parser.parse_args(["history"])
        args.history_cmd = None
        code = handle_history(args)
        assert code == 1
