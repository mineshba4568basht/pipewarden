"""Tests for pipewarden.projection."""
from datetime import datetime, timedelta
from typing import List, Tuple

import pytest

from pipewarden.projection import (
    ProjectionResult,
    _linear_regression,
    _r_squared,
    project,
)


def _ts(hours_offset: float = 0.0) -> datetime:
    base = datetime(2024, 1, 1, 0, 0, 0)
    return base + timedelta(hours=hours_offset)


def _history(n: int, slope: float = 1.0, intercept: float = 0.0) -> List[Tuple[datetime, float]]:
    """Generate perfectly linear history with *n* hourly points."""
    return [(_ts(i), slope * i + intercept) for i in range(n)]


# ---------------------------------------------------------------------------
# ProjectionResult
# ---------------------------------------------------------------------------

class TestProjectionResult:
    def test_fields_stored(self):
        r = ProjectionResult(
            pipeline="pipe",
            metric="rows",
            horizon_hours=12,
            projected_value=42.0,
            confidence=0.95,
            based_on=10,
        )
        assert r.pipeline == "pipe"
        assert r.metric == "rows"
        assert r.horizon_hours == 12
        assert r.projected_value == 42.0
        assert r.confidence == 0.95
        assert r.based_on == 10

    def test_projected_at_set_automatically(self):
        r = ProjectionResult(
            pipeline="p", metric="m", horizon_hours=1,
            projected_value=1.0, confidence=1.0, based_on=2,
        )
        assert isinstance(r.projected_at, datetime)


# ---------------------------------------------------------------------------
# _linear_regression
# ---------------------------------------------------------------------------

class TestLinearRegression:
    def test_perfect_line(self):
        xs = [0.0, 1.0, 2.0, 3.0]
        ys = [0.0, 2.0, 4.0, 6.0]  # slope=2, intercept=0
        slope, intercept = _linear_regression(xs, ys)
        assert abs(slope - 2.0) < 1e-9
        assert abs(intercept) < 1e-9

    def test_single_point_returns_zero_slope(self):
        slope, intercept = _linear_regression([5.0], [3.0])
        assert slope == 0.0
        assert intercept == 3.0

    def test_flat_line_zero_slope(self):
        xs = [0.0, 1.0, 2.0]
        ys = [5.0, 5.0, 5.0]
        slope, intercept = _linear_regression(xs, ys)
        assert abs(slope) < 1e-9
        assert abs(intercept - 5.0) < 1e-9


# ---------------------------------------------------------------------------
# _r_squared
# ---------------------------------------------------------------------------

class TestRSquared:
    def test_perfect_fit_returns_one(self):
        xs = [0.0, 1.0, 2.0]
        ys = [0.0, 1.0, 2.0]
        r2 = _r_squared(xs, ys, slope=1.0, intercept=0.0)
        assert abs(r2 - 1.0) < 1e-9

    def test_constant_y_returns_one(self):
        xs = [0.0, 1.0, 2.0]
        ys = [3.0, 3.0, 3.0]
        r2 = _r_squared(xs, ys, slope=0.0, intercept=3.0)
        assert r2 == 1.0

    def test_clamped_to_zero_on_bad_fit(self):
        xs = [0.0, 1.0, 2.0]
        ys = [0.0, 1.0, 2.0]
        # deliberately wrong coefficients
        r2 = _r_squared(xs, ys, slope=100.0, intercept=0.0)
        assert r2 == 0.0


# ---------------------------------------------------------------------------
# project
# ---------------------------------------------------------------------------

class TestProject:
    def test_returns_none_for_single_point(self):
        result = project("p", "m", [(_ts(0), 1.0)], horizon_hours=24)
        assert result is None

    def test_returns_none_for_empty_history(self):
        result = project("p", "m", [], horizon_hours=24)
        assert result is None

    def test_invalid_horizon_raises(self):
        with pytest.raises(ValueError, match="horizon_hours must be positive"):
            project("p", "m", _history(5), horizon_hours=0)

    def test_perfect_linear_projection(self):
        # slope=2, intercept=0; 5 hourly points (0–4 h)
        hist = _history(5, slope=2.0, intercept=0.0)
        result = project("pipe", "rows", hist, horizon_hours=1)
        assert result is not None
        # next point should be at x=5 → y=10
        assert abs(result.projected_value - 10.0) < 1e-6
        assert result.confidence > 0.99

    def test_based_on_reflects_history_length(self):
        result = project("p", "m", _history(7), horizon_hours=6)
        assert result is not None
        assert result.based_on == 7

    def test_pipeline_and_metric_stored(self):
        result = project("my_pipe", "latency", _history(3), horizon_hours=12)
        assert result is not None
        assert result.pipeline == "my_pipe"
        assert result.metric == "latency"

    def test_horizon_stored(self):
        result = project("p", "m", _history(4), horizon_hours=48)
        assert result is not None
        assert result.horizon_hours == 48

    def test_unsorted_history_handled(self):
        # provide history out of order
        hist = [(_ts(2), 4.0), (_ts(0), 0.0), (_ts(1), 2.0)]
        result = project("p", "m", hist, horizon_hours=1)
        assert result is not None
        assert abs(result.projected_value - 6.0) < 1e-6
