"""Event filtering — apply include/exclude predicates to alert streams."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from pipewarden.runner import AlertEvent


@dataclass
class FilterRule:
    """A named predicate that accepts or rejects an AlertEvent."""

    name: str
    predicate: Callable[[AlertEvent], bool]
    mode: str = "include"  # "include" | "exclude"

    def __post_init__(self) -> None:
        if self.mode not in ("include", "exclude"):
            raise ValueError(f"mode must be 'include' or 'exclude', got {self.mode!r}")

    def matches(self, event: AlertEvent) -> bool:
        return self.predicate(event)

    def __str__(self) -> str:
        return f"FilterRule(name={self.name!r}, mode={self.mode})"


@dataclass
class FilterResult:
    """Outcome of applying a FilterChain to a list of events."""

    accepted: List[AlertEvent] = field(default_factory=list)
    rejected: List[AlertEvent] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.accepted) + len(self.rejected)

    @property
    def acceptance_rate(self) -> float:
        if self.total == 0:
            return 1.0
        return len(self.accepted) / self.total

    def __str__(self) -> str:
        rate = f"{self.acceptance_rate * 100:.1f}%"
        return (
            f"FilterResult(accepted={len(self.accepted)}, "
            f"rejected={len(self.rejected)}, rate={rate})"
        )


@dataclass
class FilterChain:
    """Ordered chain of FilterRules applied sequentially to a stream of events."""

    rules: List[FilterRule] = field(default_factory=list)

    def add(self, rule: FilterRule) -> None:
        self.rules.append(rule)

    def apply(self, events: List[AlertEvent]) -> FilterResult:
        accepted: List[AlertEvent] = []
        rejected: List[AlertEvent] = []

        for event in events:
            kept = True
            for rule in self.rules:
                hit = rule.matches(event)
                if rule.mode == "include" and not hit:
                    kept = False
                    break
                if rule.mode == "exclude" and hit:
                    kept = False
                    break
            (accepted if kept else rejected).append(event)

        return FilterResult(accepted=accepted, rejected=rejected)

    def __len__(self) -> int:
        return len(self.rules)

    def __str__(self) -> str:
        return f"FilterChain(rules={len(self.rules)})"
