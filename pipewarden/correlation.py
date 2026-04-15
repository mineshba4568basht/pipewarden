"""Correlation analysis between pipeline check results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from pipewarden.history import HistoryEntry, HistoryStore


@dataclass
class CorrelationPair:
    """Represents a correlation score between two pipelines."""

    pipeline_a: str
    pipeline_b: str
    score: float  # -1.0 to 1.0
    sample_size: int

    def __str__(self) -> str:
        direction = "positive" if self.score > 0 else "negative" if self.score < 0 else "neutral"
        return (
            f"{self.pipeline_a} <-> {self.pipeline_b}: "
            f"{self.score:+.2f} ({direction}, n={self.sample_size})"
        )

    @property
    def is_strong(self) -> bool:
        return abs(self.score) >= 0.7


def _binary_series(entries: List[HistoryEntry]) -> List[int]:
    """Convert history entries to a binary pass/fail series (1=pass, 0=fail)."""
    return [1 if e.passed else 0 for e in entries]


def _pearson(xs: List[int], ys: List[int]) -> float:
    """Compute Pearson correlation coefficient for two equal-length series."""
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
    den_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / (den_x * den_y)


def correlate_pipelines(
    store: HistoryStore,
    limit: int = 50,
) -> List[CorrelationPair]:
    """Compute pairwise correlations for all pipelines in the store."""
    raw = store.load(limit=limit)
    by_pipeline: Dict[str, List[HistoryEntry]] = {}
    for entry in raw:
        by_pipeline.setdefault(entry.pipeline, []).append(entry)

    pipelines = sorted(by_pipeline.keys())
    pairs: List[CorrelationPair] = []

    for i, pa in enumerate(pipelines):
        for pb in pipelines[i + 1 :]:
            series_a = _binary_series(by_pipeline[pa])
            series_b = _binary_series(by_pipeline[pb])
            min_len = min(len(series_a), len(series_b))
            if min_len < 2:
                continue
            score = _pearson(series_a[:min_len], series_b[:min_len])
            pairs.append(
                CorrelationPair(
                    pipeline_a=pa,
                    pipeline_b=pb,
                    score=round(score, 4),
                    sample_size=min_len,
                )
            )

    return sorted(pairs, key=lambda p: abs(p.score), reverse=True)
