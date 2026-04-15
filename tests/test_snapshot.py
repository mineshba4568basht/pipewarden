"""Tests for pipewarden.snapshot and pipewarden.snapshot_cli."""
from __future__ import annotations

import argparse
import pytest

from pipewarden.snapshot import SnapshotEntry, SnapshotDiff, SnapshotStore
from pipewarden.snapshot_cli import build_snapshot_parser, handle_snapshot


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(tmp_path):
    return SnapshotStore(path=str(tmp_path / "snaps.json"))


@pytest.fixture()
def snapshot_parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_snapshot_parser(sub)
    return p


# ---------------------------------------------------------------------------
# SnapshotEntry
# ---------------------------------------------------------------------------

class TestSnapshotEntry:
    def test_str_contains_pipeline_and_metric(self):
        e = SnapshotEntry(pipeline="orders", metric="row_count", value=42.0)
        assert "orders/row_count" in str(e)
        assert "42.0" in str(e)

    def test_captured_at_set_automatically(self):
        e = SnapshotEntry(pipeline="p", metric="m", value=1.0)
        assert e.captured_at  # non-empty


# ---------------------------------------------------------------------------
# SnapshotDiff
# ---------------------------------------------------------------------------

class TestSnapshotDiff:
    def test_delta(self):
        d = SnapshotDiff(pipeline="p", metric="m", previous=100.0, current=120.0)
        assert d.delta == pytest.approx(20.0)

    def test_pct_change(self):
        d = SnapshotDiff(pipeline="p", metric="m", previous=100.0, current=120.0)
        assert d.pct_change == pytest.approx(20.0)

    def test_pct_change_zero_previous(self):
        d = SnapshotDiff(pipeline="p", metric="m", previous=0.0, current=5.0)
        assert d.pct_change is None

    def test_str_contains_arrow(self):
        d = SnapshotDiff(pipeline="p", metric="m", previous=10.0, current=15.0)
        assert "->" in str(d)


# ---------------------------------------------------------------------------
# SnapshotStore
# ---------------------------------------------------------------------------

class TestSnapshotStore:
    def test_save_and_latest(self, store):
        e = SnapshotEntry(pipeline="sales", metric="rows", value=500.0)
        store.save(e)
        latest = store.latest("sales", "rows")
        assert latest is not None
        assert latest.value == 500.0

    def test_latest_returns_none_when_empty(self, store):
        assert store.latest("missing", "metric") is None

    def test_diff_returns_none_when_no_previous(self, store):
        assert store.diff("p", "m", 10.0) is None

    def test_diff_returns_snapshot_diff(self, store):
        store.save(SnapshotEntry(pipeline="p", metric="m", value=100.0))
        diff = store.diff("p", "m", 110.0)
        assert diff is not None
        assert diff.delta == pytest.approx(10.0)

    def test_clear_removes_entries(self, store):
        store.save(SnapshotEntry(pipeline="p", metric="m", value=1.0))
        store.clear()
        assert store.latest("p", "m") is None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestSnapshotCLI:
    def test_capture_cmd(self, snapshot_parser, store, capsys):
        args = snapshot_parser.parse_args(["snapshot", "capture", "orders", "row_count", "99"])
        handle_snapshot(args, store=store)
        out = capsys.readouterr().out
        assert "orders/row_count" in out

    def test_diff_no_previous(self, snapshot_parser, store, capsys):
        args = snapshot_parser.parse_args(["snapshot", "diff", "orders", "row_count", "50"])
        handle_snapshot(args, store=store)
        assert "No previous snapshot" in capsys.readouterr().out

    def test_diff_with_previous(self, snapshot_parser, store, capsys):
        store.save(SnapshotEntry(pipeline="orders", metric="row_count", value=40.0))
        args = snapshot_parser.parse_args(["snapshot", "diff", "orders", "row_count", "50"])
        handle_snapshot(args, store=store)
        assert "->" in capsys.readouterr().out

    def test_clear_cmd(self, snapshot_parser, store, capsys):
        store.save(SnapshotEntry(pipeline="p", metric="m", value=1.0))
        args = snapshot_parser.parse_args(["snapshot", "clear"])
        handle_snapshot(args, store=store)
        assert store.latest("p", "m") is None
