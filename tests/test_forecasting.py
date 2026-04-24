"""Tests for pipewarden.forecasting."""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewarden.forecasting import ForecastResult, forecast
from pipewarden.history import HistoryEntry


def _entry(pipeline: str, metric: str, value: float, hours_ago: float) -> HistoryEntry:
    e = MagicMock(spec=HistoryEntry)
    e.pipeline = pipeline
    e.metric = metric
    e.value = value
    e.recorded_at = datetime(2024, 1, 1, 12, 0, 0) - timedelta(hours=hours_ago)
    return e


# ---------------------------------------------------------------------------
# ForecastResult
# ---------------------------------------------------------------------------

class TestForecastResult:
    def test_str_ok(self):
        r = ForecastResult(
            pipeline="p", metric="m", horizon_hours=24,
            predicted_value=42.5, confidence=0.95,
        )
        s = str(r)
        assert "[OK]" in s
        assert "p/m" in s
        assert "42.5" in s
        assert "0.95" in s

    def test_str_warning(self):
        r = ForecastResult(
            pipeline="p", metric="m", horizon_hours=6,
            predicted_value=float("nan"), confidence=0.0,
            warning="insufficient history",
        )
        s = str(r)
        assert "WARN" in s
        assert "insufficient history" in s


# ---------------------------------------------------------------------------
# forecast()
# ---------------------------------------------------------------------------

class TestForecast:
    def _linear_history(self, n: int = 5) -> list:
        """y = 2x + 10 — perfectly linear, R²=1."""
        return [
            _entry("pipe", "rows", 2.0 * i + 10.0, hours_ago=float(n - i))
            for i in range(n)
        ]

    def test_insufficient_history_returns_warning(self):
        entries = [_entry("pipe", "rows", 1.0, 1.0), _entry("pipe", "rows", 2.0, 0.5)]
        result = forecast("pipe", "rows", entries, horizon_hours=24, min_points=3)
        assert result.warning is not None
        assert math.isnan(result.predicted_value)
        assert result.confidence == 0.0

    def test_linear_series_high_confidence(self):
        result = forecast("pipe", "rows", self._linear_history(), horizon_hours=1)
        assert result.confidence > 0.99
        assert result.warning is None

    def test_predicted_value_is_float(self):
        result = forecast("pipe", "rows", self._linear_history(), horizon_hours=12)
        assert isinstance(result.predicted_value, float)

    def test_filters_by_pipeline_and_metric(self):
        entries = self._linear_history(5)
        # Add noise entries for a different pipeline/metric
        noise = [_entry("other", "rows", 999.0, float(i)) for i in range(5)]
        result = forecast("pipe", "rows", entries + noise, horizon_hours=1)
        assert result.confidence > 0.99

    def test_no_matching_entries_returns_warning(self):
        entries = [_entry("other", "rows", 1.0, 1.0)] * 5
        result = forecast("pipe", "rows", entries, horizon_hours=24)
        assert result.warning is not None

    def test_horizon_stored_in_result(self):
        result = forecast("pipe", "rows", self._linear_history(), horizon_hours=48)
        assert result.horizon_hours == 48

    def test_pipeline_and_metric_stored(self):
        result = forecast("pipe", "rows", self._linear_history())
        assert result.pipeline == "pipe"
        assert result.metric == "rows"

    def test_confidence_clamped_to_one(self):
        result = forecast("pipe", "rows", self._linear_history())
        assert 0.0 <= result.confidence <= 1.0
