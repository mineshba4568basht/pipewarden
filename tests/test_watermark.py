"""Tests for pipewarden.watermark and pipewarden.watermark_cli."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

import pytest

from pipewarden.watermark import (
    WatermarkEntry,
    WatermarkStore,
    check_lag,
)
from pipewarden.watermark_cli import build_watermark_parser, handle_watermark


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc(offset_seconds: float = 0.0) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=offset_seconds)


# ---------------------------------------------------------------------------
# WatermarkEntry
# ---------------------------------------------------------------------------

class TestWatermarkEntry:
    def test_fields_stored(self):
        t = _utc(60)
        entry = WatermarkEntry(pipeline="etl", event_time=t, lag_seconds=60.0)
        assert entry.pipeline == "etl"
        assert entry.event_time == t
        assert entry.lag_seconds == 60.0

    def test_recorded_at_set_automatically(self):
        entry = WatermarkEntry(pipeline="etl", event_time=_utc())
        assert entry.recorded_at is not None


# ---------------------------------------------------------------------------
# WatermarkStore
# ---------------------------------------------------------------------------

class TestWatermarkStore:
    def test_update_creates_entry(self):
        store = WatermarkStore()
        t = _utc(30)
        entry = store.update("pipe_a", t)
        assert entry.pipeline == "pipe_a"

    def test_update_advances_watermark(self):
        store = WatermarkStore()
        old = _utc(120)
        new = _utc(60)
        store.update("pipe_a", old)
        entry = store.update("pipe_a", new)
        assert entry.event_time == new

    def test_update_does_not_regress_watermark(self):
        store = WatermarkStore()
        new = _utc(60)
        old = _utc(120)
        store.update("pipe_a", new)
        entry = store.update("pipe_a", old)  # older — should not advance
        assert entry.event_time == new

    def test_get_missing_returns_none(self):
        store = WatermarkStore()
        assert store.get("missing") is None

    def test_all_returns_all_entries(self):
        store = WatermarkStore()
        store.update("a", _utc(10))
        store.update("b", _utc(20))
        assert len(store.all()) == 2

    def test_clear_specific_pipeline(self):
        store = WatermarkStore()
        store.update("a", _utc(10))
        store.update("b", _utc(10))
        removed = store.clear(pipeline="a")
        assert removed == 1
        assert store.get("a") is None
        assert store.get("b") is not None

    def test_clear_all(self):
        store = WatermarkStore()
        store.update("a", _utc(10))
        store.update("b", _utc(10))
        removed = store.clear()
        assert removed == 2
        assert store.all() == []


# ---------------------------------------------------------------------------
# check_lag
# ---------------------------------------------------------------------------

class TestCheckLag:
    def test_no_watermark_not_breached(self):
        store = WatermarkStore()
        result = check_lag(store, "pipe_x", threshold_seconds=60.0)
        assert not result.breached

    def test_lag_within_threshold_not_breached(self):
        store = WatermarkStore()
        store.update("pipe_a", _utc(30))
        wall = datetime.now(timezone.utc)
        result = check_lag(store, "pipe_a", threshold_seconds=60.0, wall_clock=wall)
        assert not result.breached

    def test_lag_exceeds_threshold_breached(self):
        store = WatermarkStore()
        store.update("pipe_a", _utc(120))
        wall = datetime.now(timezone.utc)
        result = check_lag(store, "pipe_a", threshold_seconds=60.0, wall_clock=wall)
        assert result.breached

    def test_lag_seconds_approximately_correct(self):
        store = WatermarkStore()
        store.update("pipe_a", _utc(90))
        wall = datetime.now(timezone.utc)
        result = check_lag(store, "pipe_a", threshold_seconds=300.0, wall_clock=wall)
        assert 85.0 <= result.lag_seconds <= 95.0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture
def watermark_parser() -> argparse.ArgumentParser:
    return build_watermark_parser()


class TestBuildWatermarkParser:
    def test_watermark_subcommand_registered(self, watermark_parser):
        args = watermark_parser.parse_args(["update", "pipe_a", "2024-01-01T00:00:00"])
        assert args.watermark_cmd == "update"

    def test_lag_default_threshold(self, watermark_parser):
        args = watermark_parser.parse_args(["lag", "pipe_a"])
        assert args.threshold == 300.0

    def test_lag_custom_threshold(self, watermark_parser):
        args = watermark_parser.parse_args(["lag", "pipe_a", "--threshold", "60"])
        assert args.threshold == 60.0

    def test_clear_default_pipeline_none(self, watermark_parser):
        args = watermark_parser.parse_args(["clear"])
        assert args.pipeline is None

    def test_clear_specific_pipeline(self, watermark_parser):
        args = watermark_parser.parse_args(["clear", "--pipeline", "my_pipe"])
        assert args.pipeline == "my_pipe"


class TestHandleWatermark:
    def test_update_advances_store(self, capsys):
        store = WatermarkStore()
        ns = argparse.Namespace(
            watermark_cmd="update",
            pipeline="pipe_a",
            event_time="2024-06-01T12:00:00",
        )
        handle_watermark(ns, store)
        out = capsys.readouterr().out
        assert "Watermark updated" in out

    def test_update_invalid_timestamp_prints_error(self, capsys):
        store = WatermarkStore()
        ns = argparse.Namespace(
            watermark_cmd="update",
            pipeline="pipe_a",
            event_time="not-a-date",
        )
        handle_watermark(ns, store)
        out = capsys.readouterr().out
        assert "Invalid event_time" in out

    def test_list_empty_store(self, capsys):
        store = WatermarkStore()
        ns = argparse.Namespace(watermark_cmd="list")
        handle_watermark(ns, store)
        out = capsys.readouterr().out
        assert "No watermarks" in out

    def test_no_cmd_prints_help_hint(self, capsys):
        store = WatermarkStore()
        ns = argparse.Namespace(watermark_cmd=None)
        handle_watermark(ns, store)
        out = capsys.readouterr().out
        assert "--help" in out
