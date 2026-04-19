"""Label-based classification for alert events."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pipewarden.runner import AlertEvent


@dataclass
class LabelSet:
    labels: Dict[str, str] = field(default_factory=dict)

    def add(self, key: str, value: str) -> None:
        if not key:
            raise ValueError("Label key must not be empty")
        self.labels[key] = value

    def get(self, key: str) -> Optional[str]:
        return self.labels.get(key)

    def matches(self, key: str, value: str) -> bool:
        return self.labels.get(key) == value

    def __str__(self) -> str:
        pairs = ", ".join(f"{k}={v}" for k, v in sorted(self.labels.items()))
        return f"LabelSet({pairs})"


@dataclass
class LabelRule:
    key: str
    value: str
    pipeline: Optional[str] = None
    severity: Optional[str] = None

    def applies_to(self, event: AlertEvent) -> bool:
        if self.pipeline and event.rule.pipeline != self.pipeline:
            return False
        if self.severity and event.rule.severity != self.severity:
            return False
        return True

    def __str__(self) -> str:
        return f"LabelRule({self.key}={self.value})"


@dataclass
class LabeledEvent:
    event: AlertEvent
    label_set: LabelSet

    def __str__(self) -> str:
        return f"LabeledEvent({self.event.rule.pipeline}/{self.event.check_name}, {self.label_set})"


def apply_labels(event: AlertEvent, rules: List[LabelRule]) -> LabeledEvent:
    ls = LabelSet()
    for rule in rules:
        if rule.applies_to(event):
            ls.add(rule.key, rule.value)
    return LabeledEvent(event=event, label_set=ls)


def batch_label(events: List[AlertEvent], rules: List[LabelRule]) -> List[LabeledEvent]:
    return [apply_labels(e, rules) for e in events]
