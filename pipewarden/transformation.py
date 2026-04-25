"""Transformation module for pipewarden.

Provides lightweight value transformation rules that can be applied to
metric values before they are evaluated by alert rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

_BUILT_IN_TRANSFORMS: Dict[str, Callable[[float], float]] = {
    "abs": abs,
    "negate": lambda x: -x,
    "round": round,
    "floor": lambda x: float(int(x)),
    "ceil": lambda x: float(-int(-x)),
    "log10": lambda x: __import__("math").log10(x) if x > 0 else 0.0,
    "sqrt": lambda x: __import__("math").sqrt(x) if x >= 0 else 0.0,
}


@dataclass
class TransformationRule:
    """A single named transformation applied to a numeric value."""

    name: str
    scale: float = 1.0
    offset: float = 0.0
    fn: str = "abs"  # one of the _BUILT_IN_TRANSFORMS keys

    def __post_init__(self) -> None:
        if self.fn not in _BUILT_IN_TRANSFORMS:
            raise ValueError(
                f"Unknown transform function '{self.fn}'. "
                f"Valid options: {sorted(_BUILT_IN_TRANSFORMS)}"
            )
        if self.scale == 0:
            raise ValueError("scale must be non-zero")

    def apply(self, value: float) -> float:
        """Apply scale, offset, then the named function."""
        intermediate = value * self.scale + self.offset
        return _BUILT_IN_TRANSFORMS[self.fn](intermediate)

    def __str__(self) -> str:
        return (
            f"TransformationRule(name={self.name!r}, fn={self.fn}, "
            f"scale={self.scale}, offset={self.offset})"
        )


@dataclass
class TransformResult:
    """Result of applying a transformation pipeline to a value."""

    rule_name: str
    original: float
    transformed: float
    steps: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.original != self.transformed

    def __str__(self) -> str:
        direction = "changed" if self.changed else "unchanged"
        return (
            f"[{self.rule_name}] {self.original} -> {self.transformed} ({direction})"
        )


def transform(rule: TransformationRule, value: float) -> TransformResult:
    """Apply *rule* to *value* and return a :class:`TransformResult`."""
    result = rule.apply(value)
    steps = [
        f"scale({rule.scale})",
        f"offset({rule.offset})",
        f"fn({rule.fn})",
    ]
    return TransformResult(
        rule_name=rule.name,
        original=value,
        transformed=result,
        steps=steps,
    )


def batch_transform(
    rule: TransformationRule, values: List[float]
) -> List[TransformResult]:
    """Apply *rule* to every value in *values*."""
    return [transform(rule, v) for v in values]
