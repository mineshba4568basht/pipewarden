"""Alert partitioning: split alert events into named partitions based on a key."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from pipewarden.runner import AlertEvent


@dataclass
class Partition:
    """A named bucket of alert events."""

    name: str
    events: List[AlertEvent] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.events)

    def __str__(self) -> str:  # pragma: no cover
        return f"Partition({self.name!r}, count={self.count})"


@dataclass
class PartitionResult:
    """Result of partitioning a collection of alert events."""

    partitions: Dict[str, Partition] = field(default_factory=dict)

    @property
    def partition_names(self) -> List[str]:
        return sorted(self.partitions.keys())

    @property
    def total_events(self) -> int:
        return sum(p.count for p in self.partitions.values())

    def get(self, name: str) -> Optional[Partition]:
        return self.partitions.get(name)

    def __str__(self) -> str:  # pragma: no cover
        parts = ", ".join(
            f"{n}={p.count}" for n, p in sorted(self.partitions.items())
        )
        return f"PartitionResult(total={self.total_events}, [{parts}])"


def partition_by(
    events: List[AlertEvent],
    key_fn: Callable[[AlertEvent], str],
) -> PartitionResult:
    """Partition *events* into named buckets using *key_fn*."""
    result = PartitionResult()
    for event in events:
        name = key_fn(event)
        if name not in result.partitions:
            result.partitions[name] = Partition(name=name)
        result.partitions[name].events.append(event)
    return result


def partition_by_pipeline(events: List[AlertEvent]) -> PartitionResult:
    """Convenience wrapper: partition events by pipeline name."""
    return partition_by(events, key_fn=lambda e: e.rule.pipeline)


def partition_by_severity(events: List[AlertEvent]) -> PartitionResult:
    """Convenience wrapper: partition events by alert severity."""
    return partition_by(events, key_fn=lambda e: e.rule.severity)
