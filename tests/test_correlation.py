"""Tests for pipewarden.correlation."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipewarden.correlation import (
    CorrelationPair,
    _binary_series,
    _pearson,
    correlate_pipelines,
)
from pipewarden.history import HistoryEntry, HistoryStore


def _entry(pipeline: str, passed: bool) -> HistoryEntry:
    return HistoryEntry(
        pipeline=pipeline,
        run_at=datetime.now(timezone.utc).isoformat(),
        passed=passed,
        total_checks=1,
        failed_checks=0 if passed else 1,
    )


@pytest.fixture()
def store(tmp_path: Path) -> HistoryStore:
    return HistoryStore(path=tmp_path / "history.json")


class TestCorrelationPair:
    def test_str_positive(self):
        pair = CorrelationPair("pipe_a", "pipe_b", 0.85, 10)
        assert "positive" in str(pair)
        assert "+0.85" in str(pair)

    def test_str_negative(self):
        pair = CorrelationPair("pipe_a", "pipe_b", -0.6, 10)
        assert "negative" in str(pair)

    def test_str_neutral(self):
        pair = CorrelationPair("pipe_a", "pipe_b", 0.0, 10)
        assert "neutral" in str(pair)

    def test_is_strong_true(self):
        assert CorrelationPair("a", "b", 0.9, 5).is_strong is True

    def test_is_strong_false(self):
        assert CorrelationPair("a", "b", 0.5, 5).is_strong is False

    def test_is_strong_negative(self):
        assert CorrelationPair("a", "b", -0.75, 5).is_strong is True


class TestBinarySeries:
    def test_all_pass(self):
        entries = [_entry("p", True)] * 3
        assert _binary_series(entries) == [1, 1, 1]

    def test_mixed(self):
        entries = [_entry("p", True), _entry("p", False)]
        assert _binary_series(entries) == [1, 0]


class TestPearson:
    def test_perfect_positive(self):
        assert _pearson([1, 0, 1, 0], [1, 0, 1, 0]) == pytest.approx(1.0)

    def test_perfect_negative(self):
        assert _pearson([1, 0, 1, 0], [0, 1, 0, 1]) == pytest.approx(-1.0)

    def test_no_variance_returns_zero(self):
        assert _pearson([1, 1, 1], [1, 0, 1]) == 0.0

    def test_too_short_returns_zero(self):
        assert _pearson([1], [1]) == 0.0


class TestCorrelatePipelines:
    def test_empty_store_returns_empty(self, store):
        assert correlate_pipelines(store) == []

    def test_single_pipeline_no_pairs(self, store):
        for passed in [True, False, True]:
            store.append(_entry("only", passed))
        assert correlate_pipelines(store) == []

    def test_two_pipelines_produce_one_pair(self, store):
        for passed in [True, False, True, False]:
            store.append(_entry("alpha", passed))
            store.append(_entry("beta", passed))
        pairs = correlate_pipelines(store)
        assert len(pairs) == 1
        assert pairs[0].pipeline_a == "alpha"
        assert pairs[0].pipeline_b == "beta"

    def test_correlated_failure_score_positive(self, store):
        pattern = [True, True, False, False, True, False]
        for p in pattern:
            store.append(_entry("x", p))
            store.append(_entry("y", p))
        pairs = correlate_pipelines(store)
        assert pairs[0].score > 0

    def test_sorted_by_abs_score_descending(self, store):
        for p in [True, False, True, False]:
            store.append(_entry("a", p))
            store.append(_entry("b", p))
            store.append(_entry("c", not p))
        pairs = correlate_pipelines(store)
        scores = [abs(p.score) for p in pairs]
        assert scores == sorted(scores, reverse=True)
