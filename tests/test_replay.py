"""Tests for pipewarden.replay."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pipewarden.history import HistoryEntry, HistoryStore
from pipewarden.replay import ReplayResult, replay

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(pipeline: str, passed: bool, offset_minutes: int = 0) -> HistoryEntry:
    return HistoryEntry(
        pipeline=pipeline,
        passed=passed,
        recorded_at=_NOW + timedelta(minutes=offset_minutes),
        total_checks=3,
        failed_checks=0 if passed else 1,
    )


@pytest.fixture()
def mock_store() -> MagicMock:
    store = MagicMock(spec=HistoryStore)
    store.list.return_value = [
        _entry("pipe_a", True, 0),
        _entry("pipe_a", False, 10),
        _entry("pipe_a", True, 20),
    ]
    return store


class TestReplayResult:
    def test_total_counts_all_entries(self) -> None:
        entries = [_entry("p", True), _entry("p", False)]
        r = ReplayResult(entries=entries, pipeline="p", start=_NOW, end=_NOW)
        assert r.total == 2

    def test_failures_counts_failed_entries(self) -> None:
        entries = [_entry("p", True), _entry("p", False), _entry("p", False)]
        r = ReplayResult(entries=entries, pipeline="p", start=_NOW, end=_NOW)
        assert r.failures == 2

    def test_pass_rate_full(self) -> None:
        entries = [_entry("p", True), _entry("p", True)]
        r = ReplayResult(entries=entries, pipeline="p", start=_NOW, end=_NOW)
        assert r.pass_rate == 1.0

    def test_pass_rate_partial(self) -> None:
        entries = [_entry("p", True), _entry("p", False)]
        r = ReplayResult(entries=entries, pipeline="p", start=_NOW, end=_NOW)
        assert r.pass_rate == pytest.approx(0.5)

    def test_pass_rate_empty(self) -> None:
        r = ReplayResult(entries=[], pipeline="p", start=_NOW, end=_NOW)
        assert r.pass_rate == 0.0

    def test_str_contains_pipeline(self) -> None:
        r = ReplayResult(entries=[], pipeline="my_pipe", start=_NOW, end=_NOW)
        assert "my_pipe" in str(r)

    def test_str_contains_pass_rate(self) -> None:
        entries = [_entry("p", True)]
        r = ReplayResult(entries=entries, pipeline="p", start=_NOW, end=_NOW)
        assert "100.0%" in str(r)


class TestReplayFunction:
    def test_returns_replay_result(self, mock_store: MagicMock) -> None:
        start = _NOW - timedelta(minutes=1)
        end = _NOW + timedelta(minutes=30)
        result = replay(mock_store, pipeline="pipe_a", start=start, end=end)
        assert isinstance(result, ReplayResult)

    def test_filters_by_time_window(self, mock_store: MagicMock) -> None:
        start = _NOW + timedelta(minutes=5)
        end = _NOW + timedelta(minutes=15)
        result = replay(mock_store, pipeline="pipe_a", start=start, end=end)
        assert result.total == 1
        assert result.failures == 1

    def test_all_entries_in_window(self, mock_store: MagicMock) -> None:
        start = _NOW - timedelta(minutes=1)
        end = _NOW + timedelta(minutes=25)
        result = replay(mock_store, pipeline="pipe_a", start=start, end=end)
        assert result.total == 3

    def test_empty_window_returns_zero(self, mock_store: MagicMock) -> None:
        start = _NOW + timedelta(hours=1)
        end = _NOW + timedelta(hours=2)
        result = replay(mock_store, pipeline="pipe_a", start=start, end=end)
        assert result.total == 0

    def test_pipeline_name_preserved(self, mock_store: MagicMock) -> None:
        start = _NOW - timedelta(minutes=1)
        end = _NOW + timedelta(minutes=30)
        result = replay(mock_store, pipeline="pipe_a", start=start, end=end)
        assert result.pipeline == "pipe_a"
