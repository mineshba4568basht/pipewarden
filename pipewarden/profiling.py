"""Pipeline run profiling: track and compare execution durations."""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class ProfileSample:
    pipeline: str
    check: str
    duration_ms: float
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __str__(self) -> str:
        ts = self.recorded_at.strftime("%Y-%m-%dT%H:%M:%S")
        return f"[{ts}] {self.pipeline}/{self.check} {self.duration_ms:.1f}ms"


@dataclass
class ProfileReport:
    pipeline: str
    check: str
    samples: List[float]  # durations in ms

    @property
    def count(self) -> int:
        return len(self.samples)

    @property
    def mean_ms(self) -> Optional[float]:
        return statistics.mean(self.samples) if self.samples else None

    @property
    def p95_ms(self) -> Optional[float]:
        if not self.samples:
            return None
        sorted_s = sorted(self.samples)
        idx = max(0, int(len(sorted_s) * 0.95) - 1)
        return sorted_s[idx]

    @property
    def stdev_ms(self) -> Optional[float]:
        return statistics.stdev(self.samples) if len(self.samples) >= 2 else None

    def __str__(self) -> str:
        if not self.samples:
            return f"{self.pipeline}/{self.check}: no samples"
        stdev_str = f"{self.stdev_ms:.1f}" if self.stdev_ms is not None else "n/a"
        return (
            f"{self.pipeline}/{self.check}: "
            f"n={self.count} mean={self.mean_ms:.1f}ms "
            f"p95={self.p95_ms:.1f}ms stdev={stdev_str}ms"
        )


class ProfilingStore:
    def __init__(self) -> None:
        self._samples: List[ProfileSample] = []

    def record(self, pipeline: str, check: str, duration_ms: float) -> ProfileSample:
        sample = ProfileSample(pipeline=pipeline, check=check, duration_ms=duration_ms)
        self._samples.append(sample)
        return sample

    def report(self, pipeline: str, check: str) -> ProfileReport:
        durations = [
            s.duration_ms
            for s in self._samples
            if s.pipeline == pipeline and s.check == check
        ]
        return ProfileReport(pipeline=pipeline, check=check, samples=durations)

    def all_samples(self, limit: int = 50) -> List[ProfileSample]:
        return self._samples[-limit:]

    def clear(self, pipeline: Optional[str] = None) -> int:
        before = len(self._samples)
        if pipeline:
            self._samples = [s for s in self._samples if s.pipeline != pipeline]
        else:
            self._samples.clear()
        return before - len(self._samples)
