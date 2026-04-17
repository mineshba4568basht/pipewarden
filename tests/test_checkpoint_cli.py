"""Tests for pipewarden.checkpoint_cli."""
from __future__ import annotations
import argparse
import pytest
from pipewarden.checkpoint import CheckpointEntry, CheckpointStore
from pipewarden.checkpoint_cli import build_checkpoint_parser, handle_checkpoint


@pytest.fixture
def checkpoint_parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_checkpoint_parser(sub)
    return p


@pytest.fixture
def store(tmp_path):
    return CheckpointStore(path=str(tmp_path / "cp.json"))


class TestBuildCheckpointParser:
    def test_checkpoint_subcommand_registered(self, checkpoint_parser):
        args = checkpoint_parser.parse_args(["checkpoint", "list"])
        assert args.command == "checkpoint"

    def test_list_default_limit(self, checkpoint_parser):
        args = checkpoint_parser.parse_args(["checkpoint", "list"])
        assert args.limit == 20

    def test_list_custom_limit(self, checkpoint_parser):
        args = checkpoint_parser.parse_args(["checkpoint", "list", "--limit", "5"])
        assert args.limit == 5

    def test_list_pipeline_filter(self, checkpoint_parser):
        args = checkpoint_parser.parse_args(["checkpoint", "list", "--pipeline", "my_pipe"])
        assert args.pipeline == "my_pipe"

    def test_record_stores_args(self, checkpoint_parser):
        args = checkpoint_parser.parse_args(["checkpoint", "record", "pipe1", "row_count", "123.0"])
        assert args.pipeline == "pipe1"
        assert args.check_name == "row_count"
        assert args.value == 123.0
        assert args.status == "pass"

    def test_record_custom_status(self, checkpoint_parser):
        args = checkpoint_parser.parse_args(["checkpoint", "record", "p", "c", "0", "--status", "fail"])
        assert args.status == "fail"


class TestHandleCheckpoint:
    def test_list_empty(self, capsys, store, checkpoint_parser):
        args = checkpoint_parser.parse_args(["checkpoint", "list"])
        handle_checkpoint(args, store=store)
        assert "No checkpoints" in capsys.readouterr().out

    def test_record_prints_entry(self, capsys, store, checkpoint_parser):
        args = checkpoint_parser.parse_args(["checkpoint", "record", "pipe", "nulls", "5.0"])
        handle_checkpoint(args, store=store)
        out = capsys.readouterr().out
        assert "pipe" in out
        assert "5.0" in out

    def test_list_shows_recorded(self, capsys, store, checkpoint_parser):
        store.record(CheckpointEntry(pipeline="p", check_name="c", status="pass", value=1.0))
        args = checkpoint_parser.parse_args(["checkpoint", "list"])
        handle_checkpoint(args, store=store)
        assert "p" in capsys.readouterr().out

    def test_clear_prints_count(self, capsys, store, checkpoint_parser):
        store.record(CheckpointEntry(pipeline="p", check_name="c", status="pass", value=1.0))
        args = checkpoint_parser.parse_args(["checkpoint", "clear"])
        handle_checkpoint(args, store=store)
        assert "1" in capsys.readouterr().out
