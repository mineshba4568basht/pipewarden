"""Alert routing — direct AlertEvents to named channels based on rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewarden.runner import AlertEvent


@dataclass
class RoutingRule:
    channel: str
    pipeline: Optional[str] = None   # None = match any
    severity: Optional[str] = None   # None = match any
    tags: List[str] = field(default_factory=list)

    def matches(self, event: AlertEvent) -> bool:
        if self.pipeline and event.rule.pipeline != self.pipeline:
            return False
        if self.severity and event.rule.severity != self.severity:
            return False
        if self.tags and not any(t in event.rule.tags for t in self.tags):
            return False
        return True

    def __str__(self) -> str:
        parts = [f"channel={self.channel}"]
        if self.pipeline:
            parts.append(f"pipeline={self.pipeline}")
        if self.severity:
            parts.append(f"severity={self.severity}")
        if self.tags:
            parts.append(f"tags={self.tags}")
        return f"RoutingRule({', '.join(parts)})"


@dataclass
class RoutingResult:
    event: AlertEvent
    channels: List[str]

    def routed(self) -> bool:
        return len(self.channels) > 0

    def __str__(self) -> str:
        status = "routed" if self.routed() else "unrouted"
        return f"[{status}] {self.event.rule.pipeline}/{self.event.result.check_name} -> {self.channels}"


class AlertRouter:
    def __init__(self, rules: List[RoutingRule], default_channel: str = "default") -> None:
        self.rules = rules
        self.default_channel = default_channel

    def route(self, event: AlertEvent) -> RoutingResult:
        channels = [r.channel for r in self.rules if r.matches(event)]
        if not channels:
            channels = [self.default_channel]
        return RoutingResult(event=event, channels=channels)

    def route_all(self, events: List[AlertEvent]) -> List[RoutingResult]:
        return [self.route(e) for e in events]
