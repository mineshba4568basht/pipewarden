"""Tests for pipewarden.scoring_cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipewarden.scoring_cli import build_scoring_parser, handle_scoring
from pipewarden.scoring import ScoringPolicy, ScoreResult


@pytest.fixture()
def scoring_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    build_scoring_parser(sub)
    return parser


class TestBuildScoringParser:
    def test_scoring_subcommand_registered(self, scoring_parser):
        args = scoring_parser.parse_args(["scoring", "info"])
        assert args.cmd == "scoring"

    def test_info_subcommand_exists(self, scoring_parser):
        args = scoring_parser.parse_args(["scoring", "info"])
        assert args.scoring_cmd == "info"

    def test_info_default_critical_weight(self, scoring_parser):
        args = scoring_parser.parse_args(["scoring", "info"])
        assert args.critical_weight == 40

    def test_info_default_warning_weight(self, scoring_parser):
        args = scoring_parser.parse_args(["scoring", "info"])
        assert args.warning_weight == 15

    def test_info_default_max_score(self, scoring_parser):
        args = scoring_parser.parse_args(["scoring", "info"])
        assert args.max_score == 100

    def test_score_subcommand_stores_pipeline(self, scoring_parser):
        args = scoring_parser.parse_args(["scoring", "score", "my_pipe"])
        assert args.pipeline == "my_pipe"

    def test_score_default_limit(self, scoring_parser):
        args = scoring_parser.parse_args(["scoring", "score", "p"])
        assert args.limit == 50

    def test_score_default_history_file(self, scoring_parser):
        args = scoring_parser.parse_args(["scoring", "score", "p"])
        assert args.history_file == ".pipewarden_history.json"

    def test_score_json_flag_default_false(self, scoring_parser):
        args = scoring_parser.parse_args(["scoring", "score", "p"])
        assert args.as_json is False

    def test_score_json_flag_can_be_set(self, scoring_parser):
        args = scoring_parser.parse_args(["scoring", "score", "p", "--json"])
        assert args.as_json is True


class TestHandleScoring:
    def test_info_prints_policy(self, scoring_parser, capsys):
        args = scoring_parser.parse_args(["scoring", "info"])
        handle_scoring(args)
        out = capsys.readouterr().out
        assert "ScoringPolicy" in out

    def test_score_no_events_full_score(self, scoring_parser, tmp_path, capsys):
        history_file = tmp_path / "hist.json"
        history_file.write_text("[]", encoding="utf-8")
        args = scoring_parser.parse_args(
            ["scoring", "score", "pipe_a", "--history-file", str(history_file)]
        )
        handle_scoring(args)
        out = capsys.readouterr().out
        assert "pipe_a" in out

    def test_score_json_output(self, scoring_parser, tmp_path, capsys):
        history_file = tmp_path / "hist.json"
        history_file.write_text("[]", encoding="utf-8")
        args = scoring_parser.parse_args(
            ["scoring", "score", "pipe_a",
             "--history-file", str(history_file), "--json"]
        )
        handle_scoring(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["pipeline"] == "pipe_a"
        assert "score" in data
        assert "healthy" in data
