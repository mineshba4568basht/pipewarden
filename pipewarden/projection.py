"""Metric projection: extrapolate future values from historical trend data."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class ProjectionResult:
    """Result of a forward projection for a single pipeline metric."""

    pipeline: str
    metric: str
    horizon_hours: int
    projected_value: float
    confidence: float  # 0.0 – 1.0
    based_on: int      # number of historical samples used
    projected_at: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:  # pragma: no cover
        sign = "+" if self.projected_value >= 0 else ""
        return (
            f"[{self.pipeline}/{self.metric}] "
            f"projected in {self.horizon_hours}h: {sign}{self.projected_value:.4f} "
            f"(confidence={self.confidence:.0%}, n={self.based_on})"
        )


def _linear_regression(xs: List[float], ys: List[float]) -> tuple[float, float]:
    """Return (slope, intercept) for a simple OLS linear regression."""
    n = len(xs)
    if n < 2:
        return 0.0, ys[-1] if ys else 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    ss_xx = sum((x - mean_x) ** 2 for x in xs)
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = ss_xy / ss_xx if ss_xx != 0 else 0.0
    intercept = mean_y - slope * mean_x
    return slope, intercept


def _r_squared(xs: List[float], ys: List[float], slope: float, intercept: float) -> float:
    """Return R² as a confidence proxy (clamped to [0, 1])."""
    if len(ys) < 2:
        return 0.0
    mean_y = sum(ys) / len(ys)
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    if ss_tot == 0:
        return 1.0
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    return max(0.0, min(1.0, 1.0 - ss_res / ss_tot))


def project(
    pipeline: str,
    metric: str,
    history: List[tuple[datetime, float]],
    horizon_hours: int = 24,
) -> Optional[ProjectionResult]:
    """Project *metric* forward by *horizon_hours* using linear regression.

    Parameters
    ----------
    history:
        List of (timestamp, value) pairs in any order.  At least 2 points
        are required; fewer returns ``None``.
    horizon_hours:
        How many hours into the future to project.
    """
    if len(history) < 2:
        return None

    if horizon_hours <= 0:
        raise ValueError("horizon_hours must be positive")

    sorted_history = sorted(history, key=lambda t: t[0])
    t0 = sorted_history[0][0]
    xs = [(ts - t0).total_seconds() / 3600.0 for ts, _ in sorted_history]
    ys = [v for _, v in sorted_history]

    slope, intercept = _linear_regression(xs, ys)
    confidence = _r_squared(xs, ys, slope, intercept)

    future_x = xs[-1] + horizon_hours
    projected_value = slope * future_x + intercept

    return ProjectionResult(
        pipeline=pipeline,
        metric=metric,
        horizon_hours=horizon_hours,
        projected_value=projected_value,
        confidence=confidence,
        based_on=len(history),
    )
