"""Tests for pipewarden.archiving_cli."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import pytest

from pipewarden.archiving_cli import build_archiving_parser, handle_archiving


@pytest.fixture()
def arch_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    build_archiving_parser(sub)
    return parser


class TestBuildArchivingParser:
    def test_archive_subcommand_registered(self, arch_parser):
        args = arch_parser.parse_args(["archive", "run"])
        assert args.command == "archive"

    def test_run_subcommand_stores_cmd(self, arch_parser):
        args = arch_parser.parse_args(["archive", "run"])
        assert args.archive_cmd == "run"

    def test_default_max_age_hours(self, arch_parser):
        args = arch_parser.parse_args(["archive", "run"])
        assert args.max_age_hours == 168

    def test_custom_max_age_hours(self, arch_parser):
        args = arch_parser.parse_args(["archive", "run", "--max-age-hours", "48"])
        assert args.max_age_hours == 48

    def test_default_archive_path(self, arch_parser):
        args = arch_parser.parse_args(["archive", "run"])
        assert args.archive_path == ".pipewarden_archive.jsonl.gz"

    def test_custom_archive_path(self, arch_parser):
        args = arch_parser.parse_args(["archive", "run", "--archive-path", "/tmp/a.gz"])
        assert args.archive_path == "/tmp/a.gz"


class TestHandleArchiving:
    def test_missing_history_file_prints_message(self, arch_parser, tmp_path, capsys):
        args = arch_parser.parse_args(
            ["archive", "run", "--history-file", str(tmp_path / "missing.jsonl")]
        )
        handle_archiving(args)
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_run_archives_old_entries(self, arch_parser, tmp_path, capsys):
        history = tmp_path / "history.jsonl"
        arch = tmp_path / "arch.gz"
        old_ts = "2000-01-01T00:00:00+00:00"
        history.write_text(json.dumps({"timestamp": old_ts, "pipeline": "p"}) + "\n")
        args = arch_parser.parse_args(
            [
                "archive", "run",
                "--history-file", str(history),
                "--archive-path", str(arch),
                "--max-age-hours", "24",
            ]
        )
        handle_archiving(args)
        assert arch.exists()
        with gzip.open(arch, "rb") as fh:
            lines = [l for l in fh if l.strip()]
        assert len(lines) == 1

    def test_no_archive_cmd_prints_hint(self, arch_parser, capsys):
        args = arch_parser.parse_args(["archive"])
        handle_archiving(args)
        captured = capsys.readouterr()
        assert "archive run" in captured.out
