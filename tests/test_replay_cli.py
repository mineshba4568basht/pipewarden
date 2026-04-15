"""Tests for pipewarden.replay_cli."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from pipewarden.replay_cli import build_replay_parser, handle_replay, _parse_dt


@pytest.fixture()
def replay_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    build_replay_parser(sub)
    return parser


class TestBuildReplayParser:
    def test_replay_subcommand_registered(self, replay_parser: argparse.ArgumentParser) -> None:
        args = replay_parser.parse_args(
            ["replay", "run", "my_pipe", "--start", "2024-06-01T00:00:00"]
        )
        assert args.command == "replay"

    def test_run_subcommand_stores_pipeline(self, replay_parser: argparse.ArgumentParser) -> None:
        args = replay_parser.parse_args(
            ["replay", "run", "pipe_x", "--start", "2024-06-01T00:00:00"]
        )
        assert args.pipeline == "pipe_x"

    def test_default_limit_is_100(self, replay_parser: argparse.ArgumentParser) -> None:
        args = replay_parser.parse_args(
            ["replay", "run", "p", "--start", "2024-06-01T00:00:00"]
        )
        assert args.limit == 100

    def test_custom_limit(self, replay_parser: argparse.ArgumentParser) -> None:
        args = replay_parser.parse_args(
            ["replay", "run", "p", "--start", "2024-06-01T00:00:00", "--limit", "50"]
        )
        assert args.limit == 50

    def test_end_defaults_to_none(self, replay_parser: argparse.ArgumentParser) -> None:
        args = replay_parser.parse_args(
            ["replay", "run", "p", "--start", "2024-06-01T00:00:00"]
        )
        assert args.end is None

    def test_history_file_default(self, replay_parser: argparse.ArgumentParser) -> None:
        args = replay_parser.parse_args(
            ["replay", "run", "p", "--start", "2024-06-01T00:00:00"]
        )
        assert args.history_file == ".pipewarden_history.json"


class TestParseDt:
    def test_parses_valid_datetime(self) -> None:
        dt = _parse_dt("2024-06-01T12:30:00")
        assert dt == datetime(2024, 6, 1, 12, 30, 0, tzinfo=timezone.utc)

    def test_raises_on_invalid_format(self) -> None:
        with pytest.raises(ValueError):
            _parse_dt("not-a-date")


class TestHandleReplay:
    def test_run_cmd_calls_replay(self, replay_parser: argparse.ArgumentParser, capsys) -> None:
        from pipewarden.replay import ReplayResult
        from datetime import datetime, timezone

        fake_result = MagicMock(spec=ReplayResult)
        fake_result.total = 0
        fake_result.__str__ = lambda self: "ReplayResult(pipeline='p', total=0, failures=0, pass_rate=0.0%)"

        args = replay_parser.parse_args(
            ["replay", "run", "p", "--start", "2024-06-01T00:00:00"]
        )

        with patch("pipewarden.replay_cli.HistoryStore") as MockStore, \
             patch("pipewarden.replay_cli.replay", return_value=fake_result) as mock_replay:
            handle_replay(args)
            mock_replay.assert_called_once()

    def test_no_entries_prints_message(self, replay_parser: argparse.ArgumentParser, capsys) -> None:
        from pipewarden.replay import ReplayResult

        fake_result = MagicMock(spec=ReplayResult)
        fake_result.total = 0
        fake_result.__str__ = lambda self: "ReplayResult()"
        fake_result.entries = []

        args = replay_parser.parse_args(
            ["replay", "run", "p", "--start", "2024-06-01T00:00:00"]
        )

        with patch("pipewarden.replay_cli.HistoryStore"), \
             patch("pipewarden.replay_cli.replay", return_value=fake_result):
            handle_replay(args)

        captured = capsys.readouterr()
        assert "No entries" in captured.out
