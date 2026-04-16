"""Alert event enrichment — attach metadata to AlertEvents before dispatch."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Callable

from pipewarden.runner import AlertEvent


@dataclass
class EnrichedEvent:
    event: AlertEvent
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        meta_str = ", ".join(f"{k}={v}" for k, v in self.metadata.items())
        return f"EnrichedEvent({self.event.rule.name} meta=[{meta_str}])"


Enricher = Callable[[AlertEvent, Dict[str, Any]], None]


def _enrich_environment(event: AlertEvent, meta: Dict[str, Any]) -> None:
    import os
    meta["env"] = os.environ.get("PIPEWARDEN_ENV", "production")


def _enrich_hostname(event: AlertEvent, meta: Dict[str, Any]) -> None:
    import socket
    try:
        meta["host"] = socket.gethostname()
    except Exception:
        meta["host"] = "unknown"


def _enrich_severity(event: AlertEvent, meta: Dict[str, Any]) -> None:
    meta["severity"] = event.rule.severity


DEFAULT_ENRICHERS: List[Enricher] = [
    _enrich_environment,
    _enrich_hostname,
    _enrich_severity,
]


class EventEnricher:
    """Applies a chain of enricher functions to produce EnrichedEvents."""

    def __init__(self, enrichers: List[Enricher] | None = None) -> None:
        self._enrichers: List[Enricher] = enrichers if enrichers is not None else list(DEFAULT_ENRICHERS)

    def add(self, enricher: Enricher) -> None:
        self._enrichers.append(enricher)

    def enrich(self, event: AlertEvent) -> EnrichedEvent:
        meta: Dict[str, Any] = {}
        for fn in self._enrichers:
            fn(event, meta)
        return EnrichedEvent(event=event, metadata=meta)

    def enrich_all(self, events: List[AlertEvent]) -> List[EnrichedEvent]:
        return [self.enrich(e) for e in events]
