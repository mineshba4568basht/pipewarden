"""Load shedding: drop low-priority alerts when the system is under pressure."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from pipewarden.runner import AlertEvent


@dataclass
class SheddingPolicy:
    """Policy that defines when and how to shed alert load."""

    max_queue_depth: int = 100
    min_priority: int = 0  # 0 = shed nothing by default
    shed_on_overload: bool = True

    def __post_init__(self) -> None:
        if self.max_queue_depth < 1:
            raise ValueError("max_queue_depth must be >= 1")
        if not (0 <= self.min_priority <= 10):
            raise ValueError("min_priority must be between 0 and 10")

    def __str__(self) -> str:
        return (
            f"SheddingPolicy(max_queue_depth={self.max_queue_depth}, "
            f"min_priority={self.min_priority}, "
            f"shed_on_overload={self.shed_on_overload})"
        )


@dataclass
class ShedResult:
    """Result of applying load shedding to a batch of events."""

    accepted: List[AlertEvent] = field(default_factory=list)
    shed: List[AlertEvent] = field(default_factory=list)
    evaluated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def total(self) -> int:
        return len(self.accepted) + len(self.shed)

    @property
    def shed_count(self) -> int:
        return len(self.shed)

    def __str__(self) -> str:
        return (
            f"ShedResult(total={self.total}, accepted={len(self.accepted)}, "
            f"shed={self.shed_count})"
        )


def _priority_of(event: AlertEvent) -> int:
    """Derive a numeric priority from an event's severity (higher = more important)."""
    mapping = {"critical": 10, "warning": 5, "info": 1}
    severity = getattr(event.rule, "severity", "info")
    return mapping.get(severity, 0)


def apply_shedding(
    events: List[AlertEvent],
    policy: SheddingPolicy,
    current_queue_depth: int = 0,
) -> ShedResult:
    """Apply the shedding policy to *events* given the current queue depth."""
    result = ShedResult()
    overloaded = policy.shed_on_overload and current_queue_depth >= policy.max_queue_depth

    for event in events:
        priority = _priority_of(event)
        if overloaded and priority < policy.min_priority:
            result.shed.append(event)
        else:
            result.accepted.append(event)

    return result
