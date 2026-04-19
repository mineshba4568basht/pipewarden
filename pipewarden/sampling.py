"""Alert sampling — probabilistic and rate-based sampling of alert events."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List

from pipewarden.runner import AlertEvent


@dataclass
class SamplingPolicy:
    """Controls what fraction of alert events are forwarded."""
    rate: float = 1.0          # 0.0 – 1.0; 1.0 means keep everything
    seed: int | None = None    # optional seed for reproducibility

    def __post_init__(self) -> None:
        if not (0.0 < self.rate <= 1.0):
            raise ValueError("rate must be in the range (0, 1]")
        self._rng = random.Random(self.seed)

    def __str__(self) -> str:
        return f"SamplingPolicy(rate={self.rate:.0%})"


@dataclass
class SampleResult:
    event: AlertEvent
    kept: bool
    rate: float

    def __str__(self) -> str:
        status = "KEPT" if self.kept else "DROPPED"
        return f"[{status}] {self.event.rule.name} @ {self.event.pipeline} (rate={self.rate:.0%})"


def sample_event(event: AlertEvent, policy: SamplingPolicy) -> SampleResult:
    """Decide whether a single event passes the sampling filter."""
    kept = policy._rng.random() < policy.rate
    return SampleResult(event=event, kept=kept, rate=policy.rate)


def batch_sample(events: List[AlertEvent], policy: SamplingPolicy) -> List[SampleResult]:
    """Apply sampling to a list of events and return all results."""
    return [sample_event(e, policy) for e in events]


def kept_events(results: List[SampleResult]) -> List[AlertEvent]:
    """Return only the events that were kept."""
    return [r.event for r in results if r.kept]
