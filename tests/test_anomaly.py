"""Tests for pipewarden.anomaly and pipewarden.anomaly_cli."""
from __future__ import annotations

import argparse
import json
from io import StringIO
from unittest.mock import patch

import pytest

from pipewarden.anomaly import AnomalyResult, batch_detect, detect_anomaly
from pipewarden.anomaly_cli import build_anomaly_parser, handle_anomaly


# ---------------------------------------------------------------------------
# detect_anomaly
# ---------------------------------------------------------------------------

class TestDetectAnomaly:
    def test_no_history_returns_non_anomaly(self):
        r = detect_anomaly("pipe", "rows", 100.0, [])
        assert not r.is_anomaly
        assert r.z_score == 0.0

    def test_single_history_returns_non_anomaly(self):
        r = detect_anomaly("pipe", "rows", 100.0, [95.0])
        assert not r.is_anomaly

    def test_normal_value_not_anomaly(self):
        history = [100.0, 102.0, 98.0, 101.0, 99.0]
        r = detect_anomaly("pipe", "rows", 100.5, history)
        assert not r.is_anomaly

    def test_extreme_value_is_anomaly(self):
        history = [100.0, 101.0, 99.0, 100.5, 100.2]
        r = detect_anomaly("pipe", "rows", 500.0, history, threshold=3.0)
        assert r.is_anomaly
        assert r.z_score > 3.0

    def test_constant_history_no_anomaly(self):
        history = [50.0, 50.0, 50.0]
        r = detect_anomaly("pipe", "rows", 50.0, history)
        assert not r.is_anomaly
        assert r.stddev == 0.0

    def test_result_fields_populated(self):
        history = [10.0, 12.0, 11.0, 9.0, 10.5]
        r = detect_anomaly("mypipe", "latency", 11.0, history)
        assert r.pipeline == "mypipe"
        assert r.metric == "latency"
        assert r.value == 11.0
        assert r.mean > 0
        assert r.stddev >= 0

    def test_custom_threshold(self):
        history = [100.0] * 10
        # stddev is 0, so z_score is 0 — not an anomaly regardless of threshold
        r = detect_anomaly("p", "m", 101.0, history, threshold=0.5)
        assert not r.is_anomaly


# ---------------------------------------------------------------------------
# AnomalyResult.__str__
# ---------------------------------------------------------------------------

class TestAnomalyResultStr:
    def test_str_ok(self):
        r = AnomalyResult("p", "m", 1.0, 1.0, 0.0, 0.0, 3.0, False)
        assert "OK" in str(r)
        assert "p/m" in str(r)

    def test_str_anomaly(self):
        r = AnomalyResult("p", "m", 999.0, 1.0, 0.5, 10.0, 3.0, True)
        assert "ANOMALY" in str(r)


# ---------------------------------------------------------------------------
# batch_detect
# ---------------------------------------------------------------------------

class TestBatchDetect:
    def test_returns_result_per_metric(self):
        metrics = {"rows": 100.0, "latency": 5.0}
        history_map = {
            "rows": [98.0, 100.0, 102.0],
            "latency": [4.8, 5.0, 5.2],
        }
        results = batch_detect("pipe", metrics, history_map)
        assert len(results) == 2

    def test_missing_history_treated_as_empty(self):
        results = batch_detect("pipe", {"rows": 50.0}, {})
        assert len(results) == 1
        assert not results[0].is_anomaly


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture
def anomaly_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    build_anomaly_parser(sub)
    return parser


class TestAnomalyCli:
    def test_check_normal_exits_zero(self, anomaly_parser, capsys):
        args = anomaly_parser.parse_args(
            ["anomaly", "check", "mypipe", "rows", "100",
             "--history", "98", "100", "102"]
        )
        handle_anomaly(args)  # should not raise SystemExit

    def test_check_anomaly_exits_one(self, anomaly_parser):
        args = anomaly_parser.parse_args(
            ["anomaly", "check", "mypipe", "rows", "9999",
             "--history", "100", "101", "99", "100", "100"]
        )
        with pytest.raises(SystemExit) as exc:
            handle_anomaly(args)
        assert exc.value.code == 1

    def test_check_json_output(self, anomaly_parser, capsys):
        args = anomaly_parser.parse_args(
            ["anomaly", "check", "mypipe", "rows", "100",
             "--history", "98", "100", "102", "--json"]
        )
        handle_anomaly(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["pipeline"] == "mypipe"
        assert "is_anomaly" in data
