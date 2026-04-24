"""Simple metric forecasting using linear extrapolation over history."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Sequence

from pipewarden.history import HistoryEntry


@dataclass
class ForecastResult:
    pipeline: str
    metric: str
    horizon_hours: int
    predicted_value: float
    confidence: float          # 0.0 – 1.0, based on R²
    forecasted_at: datetime = field(default_factory=datetime.utcnow)
    warning: Optional[str] = None

    def __str__(self) -> str:  # noqa: D401
        status = "OK" if self.warning is None else f"WARN:{self.warning}"
        return (
            f"[{status}] {self.pipeline}/{self.metric} "
            f"in {self.horizon_hours}h → {self.predicted_value:.4f} "
            f"(confidence={self.confidence:.2f})"
        )


def _linear_fit(xs: List[float], ys: List[float]) -> tuple[float, float]:
    """Return (slope, intercept) for the least-squares line."""
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    slope = num / den if den != 0 else 0.0
    intercept = mean_y - slope * mean_x
    return slope, intercept


def _r_squared(xs: List[float], ys: List[float], slope: float, intercept: float) -> float:
    mean_y = sum(ys) / len(ys)
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    return 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0


def forecast(
    pipeline: str,
    metric: str,
    history: Sequence[HistoryEntry],
    horizon_hours: int = 24,
    min_points: int = 3,
) -> ForecastResult:
    """Forecast *metric* for *pipeline* by linearly extrapolating *history*."""
    relevant = [
        e for e in history
        if e.pipeline == pipeline and e.metric == metric
    ]
    relevant.sort(key=lambda e: e.recorded_at)

    if len(relevant) < min_points:
        return ForecastResult(
            pipeline=pipeline,
            metric=metric,
            horizon_hours=horizon_hours,
            predicted_value=float("nan"),
            confidence=0.0,
            warning=f"insufficient history ({len(relevant)}/{min_points} points)",
        )

    origin = relevant[0].recorded_at
    xs = [(e.recorded_at - origin).total_seconds() / 3600.0 for e in relevant]
    ys = [e.value for e in relevant]

    slope, intercept = _linear_fit(xs, ys)
    r2 = _r_squared(xs, ys, slope, intercept)

    horizon_x = (relevant[-1].recorded_at - origin).total_seconds() / 3600.0 + horizon_hours
    predicted = slope * horizon_x + intercept

    return ForecastResult(
        pipeline=pipeline,
        metric=metric,
        horizon_hours=horizon_hours,
        predicted_value=round(predicted, 6),
        confidence=round(max(0.0, min(1.0, r2)), 4),
    )
