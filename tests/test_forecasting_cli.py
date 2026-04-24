"""Tests for pipewarden.forecasting_cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipewarden.forecasting_cli import build_forecasting_parser, handle_forecasting
from pipewarden.forecasting import ForecastResult


@pytest.fixture()
def forecasting_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_forecasting_parser(sub)
    return root


class TestBuildForecastingParser:
    def test_forecast_subcommand_registered(self, forecasting_parser):
        args = forecasting_parser.parse_args(["forecast", "run",
                                               "--pipeline", "p", "--metric", "m"])
        assert args.command == "forecast"

    def test_run_stores_pipeline(self, forecasting_parser):
        args = forecasting_parser.parse_args(["forecast", "run",
                                               "--pipeline", "mypipe", "--metric", "rows"])
        assert args.pipeline == "mypipe"

    def test_run_stores_metric(self, forecasting_parser):
        args = forecasting_parser.parse_args(["forecast", "run",
                                               "--pipeline", "p", "--metric", "latency"])
        assert args.metric == "latency"

    def test_default_horizon_is_24(self, forecasting_parser):
        args = forecasting_parser.parse_args(["forecast", "run",
                                               "--pipeline", "p", "--metric", "m"])
        assert args.horizon == 24

    def test_custom_horizon(self, forecasting_parser):
        args = forecasting_parser.parse_args(["forecast", "run",
                                               "--pipeline", "p", "--metric", "m",
                                               "--horizon", "48"])
        assert args.horizon == 48

    def test_default_min_points_is_3(self, forecasting_parser):
        args = forecasting_parser.parse_args(["forecast", "run",
                                               "--pipeline", "p", "--metric", "m"])
        assert args.min_points == 3

    def test_json_flag_default_false(self, forecasting_parser):
        args = forecasting_parser.parse_args(["forecast", "run",
                                               "--pipeline", "p", "--metric", "m"])
        assert args.json is False

    def test_json_flag_true(self, forecasting_parser):
        args = forecasting_parser.parse_args(["forecast", "run",
                                               "--pipeline", "p", "--metric", "m",
                                               "--json"])
        assert args.json is True


class TestHandleForecasting:
    def _make_args(self, json_output: bool = False) -> argparse.Namespace:
        return argparse.Namespace(
            forecast_cmd="run",
            pipeline="pipe",
            metric="rows",
            horizon=24,
            min_points=3,
            history_file="dummy.json",
            json=json_output,
        )

    def _fake_result(self) -> ForecastResult:
        return ForecastResult(
            pipeline="pipe", metric="rows",
            horizon_hours=24, predicted_value=55.0, confidence=0.98,
        )

    def test_run_prints_str(self, capsys):
        with patch("pipewarden.forecasting_cli.HistoryStore") as MockStore, \
             patch("pipewarden.forecasting_cli.forecast", return_value=self._fake_result()):
            MockStore.return_value.all.return_value = []
            handle_forecasting(self._make_args(json_output=False))
        out = capsys.readouterr().out
        assert "pipe/rows" in out

    def test_run_json_output(self, capsys):
        with patch("pipewarden.forecasting_cli.HistoryStore") as MockStore, \
             patch("pipewarden.forecasting_cli.forecast", return_value=self._fake_result()):
            MockStore.return_value.all.return_value = []
            handle_forecasting(self._make_args(json_output=True))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["pipeline"] == "pipe"
        assert data["predicted_value"] == pytest.approx(55.0)

    def test_no_subcommand_prints_help(self, capsys):
        args = argparse.Namespace(forecast_cmd=None)
        handle_forecasting(args)
        out = capsys.readouterr().out
        assert "help" in out.lower() or "usage" in out.lower() or "forecast" in out.lower()
