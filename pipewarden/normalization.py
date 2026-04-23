"""Value normalization for pipeline check results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class NormalizationRule:
    """Defines how a named metric should be normalized."""

    metric: str
    strategy: str = "minmax"  # minmax | zscore | clamp
    min_val: float = 0.0
    max_val: float = 1.0
    clamp_low: Optional[float] = None
    clamp_high: Optional[float] = None

    def __post_init__(self) -> None:
        valid = {"minmax", "zscore", "clamp"}
        if self.strategy not in valid:
            raise ValueError(f"strategy must be one of {valid}, got {self.strategy!r}")
        if self.strategy == "minmax" and self.max_val <= self.min_val:
            raise ValueError("max_val must be greater than min_val")

    def __str__(self) -> str:
        return f"NormalizationRule(metric={self.metric!r}, strategy={self.strategy})"


@dataclass
class NormalizeResult:
    """Outcome of normalizing a single value."""

    metric: str
    raw: float
    normalized: float
    strategy: str

    def __str__(self) -> str:
        return (
            f"NormalizeResult({self.metric}: {self.raw} -> {self.normalized:.4f} "
            f"[{self.strategy}])"
        )


def _minmax(value: float, min_val: float, max_val: float) -> float:
    span = max_val - min_val
    return (value - min_val) / span if span else 0.0


def _zscore(value: float, history: List[float]) -> float:
    if len(history) < 2:
        return 0.0
    mean = sum(history) / len(history)
    variance = sum((x - mean) ** 2 for x in history) / len(history)
    std = variance ** 0.5
    return (value - mean) / std if std else 0.0


def _clamp(value: float, low: Optional[float], high: Optional[float]) -> float:
    if low is not None:
        value = max(low, value)
    if high is not None:
        value = min(high, value)
    return value


def normalize(
    rule: NormalizationRule,
    value: float,
    history: Optional[List[float]] = None,
) -> NormalizeResult:
    """Apply *rule* to *value*, using *history* for z-score strategy."""
    if rule.strategy == "minmax":
        normalized = _minmax(value, rule.min_val, rule.max_val)
    elif rule.strategy == "zscore":
        normalized = _zscore(value, history or [])
    else:  # clamp
        normalized = _clamp(value, rule.clamp_low, rule.clamp_high)

    return NormalizeResult(
        metric=rule.metric,
        raw=value,
        normalized=normalized,
        strategy=rule.strategy,
    )


def batch_normalize(
    rules: List[NormalizationRule],
    values: Dict[str, float],
    history: Optional[Dict[str, List[float]]] = None,
) -> List[NormalizeResult]:
    """Normalize multiple metrics using their respective rules."""
    history = history or {}
    rule_map = {r.metric: r for r in rules}
    results: List[NormalizeResult] = []
    for metric, value in values.items():
        if metric in rule_map:
            results.append(normalize(rule_map[metric], value, history.get(metric)))
    return results
