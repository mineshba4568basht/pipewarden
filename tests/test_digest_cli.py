"""Tests for pipewarden.digest_cli module."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pipewarden.digest_cli import build_digest_parser, handle_digest
from pipewarden.digest import DigestReport, DigestEntry
from pipewarden.trend import TrendSummary


@pytest.fixture()
def digest_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    build_digest_parser(subs)
    return root


@pytest.fixture()
def history_file(tmp_path: Path) -> str:
    now = datetime.utcnow()
    entries = [
        {
            "pipeline": "demo",
            "passed": True,
            "run_at": (now - timedelta(hours=1)).isoformat(),
            "check_count": 2,
            "failed_checks": 0,
        }
    ]
    path = tmp_path / "hist.json"
    path.write_text(json.dumps(entries))
    return str(path)


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------

class TestBuildDigestParser:
    def test_digest_subcommand_registered(self, digest_parser: argparse.ArgumentParser):
        args = digest_parser.parse_args(["digest"])
        assert hasattr(args, "func")

    def test_default_period_is_24(self, digest_parser: argparse.ArgumentParser):
        args = digest_parser.parse_args(["digest"])
        assert args.period == 24

    def test_custom_period(self, digest_parser: argparse.ArgumentParser):
        args = digest_parser.parse_args(["digest", "--period", "48"])
        assert args.period == 48

    def test_pipeline_filter_default_none(self, digest_parser: argparse.ArgumentParser):
        args = digest_parser.parse_args(["digest"])
        assert args.pipeline is None

    def test_pipeline_filter_set(self, digest_parser: argparse.ArgumentParser):
        args = digest_parser.parse_args(["digest", "--pipeline", "my_pipe"])
        assert args.pipeline == "my_pipe"

    def test_history_file_default(self, digest_parser: argparse.ArgumentParser):
        args = digest_parser.parse_args(["digest"])
        assert args.history_file == ".pipewarden_history.json"


# ---------------------------------------------------------------------------
# handle_digest
# ---------------------------------------------------------------------------

def _make_trend(cf: int = 0) -> TrendSummary:
    return TrendSummary(pipeline="demo", total=1, passed=1 - cf, failed=cf,
                        consecutive_failures=cf, pass_rate=1.0 - cf)


class TestHandleDigest:
    def test_prints_report_for_valid_history(self, history_file: str, capsys):
        args = argparse.Namespace(
            history_file=history_file,
            period=24,
            pipeline=None,
        )
        handle_digest(args)
        captured = capsys.readouterr()
        assert "PipeWarden Digest" in captured.out

    def test_exits_0_when_all_healthy(self, history_file: str):
        args = argparse.Namespace(
            history_file=history_file,
            period=24,
            pipeline=None,
        )
        # All entries pass → no degraded pipelines → exit 0 (no SystemExit)
        handle_digest(args)  # should not raise

    def test_exits_1_when_degraded(self, history_file: str):
        degraded_entry = DigestEntry("demo", 2, 1, 1, _make_trend(1))
        mock_report = DigestReport(entries=[degraded_entry])
        args = argparse.Namespace(
            history_file=history_file,
            period=24,
            pipeline=None,
        )
        with patch("pipewarden.digest_cli.build_digest", return_value=mock_report):
            with pytest.raises(SystemExit) as exc_info:
                handle_digest(args)
            assert exc_info.value.code == 1

    def test_pipeline_filter_applied(self, history_file: str, capsys):
        args = argparse.Namespace(
            history_file=history_file,
            period=24,
            pipeline="nonexistent",
        )
        with pytest.raises(SystemExit) as exc_info:
            handle_digest(args)
        assert exc_info.value.code == 0
