"""Alert grouping – bucket AlertEvents by a key and emit one grouped record."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from pipewarden.runner import AlertEvent


@dataclass
class AlertGroup:
    key: str
    events: List[AlertEvent] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.events)

    @property
    def severities(self) -> List[str]:
        return [e.rule.severity for e in self.events]

    @property
    def highest_severity(self) -> str:
        order = ["critical", "warning", "info"]
        for level in order:
            if level in self.severities:
                return level
        return "info"

    def __str__(self) -> str:
        return (
            f"AlertGroup(key={self.key!r}, count={self.count}, "
            f"highest={self.highest_severity})"
        )


KeyFn = Callable[[AlertEvent], str]


def group_by_pipeline(event: AlertEvent) -> str:
    return event.pipeline


def group_by_severity(event: AlertEvent) -> str:
    return event.rule.severity


def group_by_check(event: AlertEvent) -> str:
    return event.result.check_name


def group_events(
    events: List[AlertEvent],
    key_fn: KeyFn = group_by_pipeline,
) -> Dict[str, AlertGroup]:
    """Partition *events* into AlertGroups using *key_fn*."""
    groups: Dict[str, AlertGroup] = {}
    for event in events:
        key = key_fn(event)
        if key not in groups:
            groups[key] = AlertGroup(key=key)
        groups[key].events.append(event)
    return groups
