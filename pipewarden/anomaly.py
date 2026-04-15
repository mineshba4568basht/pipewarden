"""Anomaly detection for pipeline metrics using z-score analysis."""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AnomalyResult:
    pipeline: str
    metric: str
    value: float
    mean: float
    stddev: float
    z_score: float
    threshold: float
    is_anomaly: bool

    def __str__(self) -> str:
        status = "ANOMALY" if self.is_anomaly else "OK"
        return (
            f"[{status}] {self.pipeline}/{self.metric} "
            f"value={self.value:.4f} z={self.z_score:.2f} "
            f"(mean={self.mean:.4f}, stddev={self.stddev:.4f})"
        )


def detect_anomaly(
    pipeline: str,
    metric: str,
    value: float,
    history: List[float],
    threshold: float = 3.0,
) -> AnomalyResult:
    """Detect whether *value* is anomalous given historical observations.

    Uses a z-score approach.  Requires at least two historical data points;
    if fewer are available the result is always non-anomalous.
    """
    if len(history) < 2:
        return AnomalyResult(
            pipeline=pipeline,
            metric=metric,
            value=value,
            mean=float(history[0]) if history else value,
            stddev=0.0,
            z_score=0.0,
            threshold=threshold,
            is_anomaly=False,
        )

    mean = statistics.mean(history)
    stddev = statistics.pstdev(history)

    if stddev == 0.0:
        z_score = 0.0
    else:
        z_score = abs(value - mean) / stddev

    return AnomalyResult(
        pipeline=pipeline,
        metric=metric,
        value=value,
        mean=mean,
        stddev=stddev,
        z_score=z_score,
        threshold=threshold,
        is_anomaly=z_score > threshold,
    )


def batch_detect(
    pipeline: str,
    metrics: dict,
    history_map: dict,
    threshold: float = 3.0,
) -> List[AnomalyResult]:
    """Run anomaly detection for multiple metrics at once.

    *metrics* maps metric name -> current value.
    *history_map* maps metric name -> list of historical values.
    """
    results: List[AnomalyResult] = []
    for metric, value in metrics.items():
        hist = history_map.get(metric, [])
        results.append(detect_anomaly(pipeline, metric, value, hist, threshold))
    return results
