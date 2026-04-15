"""Tests for pipewarden.retention_cli."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pipewarden.history import HistoryEntry, HistoryStore
from pipewarden.retention import PruneResult
from pipewarden.retention_cli import build_retention_parser, handle_retention


@pytest.fixture()
def retention_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_retention_parser(sub)
    return p


class TestBuildRetentionParser:
    def test_retention_subcommand_registered(self, retention_parser: argparse.ArgumentParser) -> None:
        args = retention_parser.parse_args(["retention", "info"])
        assert args.command == "retention"

    def test_prune_subcommand_exists(self, retention_parser: argparse.ArgumentParser) -> None:
        args = retention_parser.parse_args(["retention", "prune"])
        assert args.retention_cmd == "prune"

    def test_prune_default_max_age(self, retention_parser: argparse.ArgumentParser) -> None:
        args = retention_parser.parse_args(["retention", "prune"])
        assert args.max_age_hours == 168

    def test_prune_custom_max_age(self, retention_parser: argparse.ArgumentParser) -> None:
        args = retention_parser.parse_args(["retention", "prune", "--max-age-hours", "48"])
        assert args.max_age_hours == 48

    def test_prune_custom_max_entries(self, retention_parser: argparse.ArgumentParser) -> None:
        args = retention_parser.parse_args(["retention", "prune", "--max-entries", "50"])
        assert args.max_entries == 50

    def test_info_subcommand_exists(self, retention_parser: argparse.ArgumentParser) -> None:
        args = retention_parser.parse_args(["retention", "info"])
        assert args.retention_cmd == "info"


class TestHandleRetention:
    def test_prune_prints_result(self, retention_parser: argparse.ArgumentParser, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        history_file = tmp_path / "history.json"
        store = HistoryStore(path=history_file)
        recent = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        store.save([HistoryEntry(pipeline="p", passed=True, timestamp=recent, checks_run=1, checks_failed=0)])

        args = retention_parser.parse_args([
            "retention", "prune",
            "--history-file", str(history_file),
            "--max-age-hours", "168",
        ])
        handle_retention(args)
        out = capsys.readouterr().out
        assert "remaining" in out

    def test_info_prints_policy(self, retention_parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture) -> None:
        args = retention_parser.parse_args(["retention", "info", "--max-age-hours", "72", "--max-entries", "200"])
        handle_retention(args)
        out = capsys.readouterr().out
        assert "72" in out
        assert "200" in out
