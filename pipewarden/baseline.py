"""Baseline management: capture and compare metric baselines for drift detection."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class BaselineEntry:
    pipeline: str
    metric: str
    value: float
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __str__(self) -> str:
        return f"[{self.captured_at}] {self.pipeline}/{self.metric} = {self.value}"


@dataclass
class BaselineDrift:
    pipeline: str
    metric: str
    baseline_value: float
    current_value: float
    threshold_pct: float

    @property
    def delta(self) -> float:
        return self.current_value - self.baseline_value

    @property
    def pct_change(self) -> Optional[float]:
        if self.baseline_value == 0:
            return None
        return (self.delta / abs(self.baseline_value)) * 100

    @property
    def is_drifted(self) -> bool:
        pct = self.pct_change
        if pct is None:
            return False
        return abs(pct) > self.threshold_pct

    def __str__(self) -> str:
        pct = self.pct_change
        pct_str = f"{pct:.1f}%" if pct is not None else "N/A"
        status = "DRIFTED" if self.is_drifted else "OK"
        return f"{self.pipeline}/{self.metric}: {self.baseline_value} -> {self.current_value} ({pct_str}) [{status}]"


class BaselineStore:
    def __init__(self, path: str = ".pipewarden_baselines.json") -> None:
        self._path = path
        self._data: Dict[str, Dict[str, BaselineEntry]] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path, "r") as fh:
            raw = json.load(fh)
        for pipeline, metrics in raw.items():
            self._data[pipeline] = {
                metric: BaselineEntry(**entry)
                for metric, entry in metrics.items()
            }

    def _save(self) -> None:
        serialisable = {
            pipeline: {
                metric: entry.__dict__
                for metric, entry in metrics.items()
            }
            for pipeline, metrics in self._data.items()
        }
        with open(self._path, "w") as fh:
            json.dump(serialisable, fh, indent=2)

    def set(self, pipeline: str, metric: str, value: float) -> BaselineEntry:
        entry = BaselineEntry(pipeline=pipeline, metric=metric, value=value)
        self._data.setdefault(pipeline, {})[metric] = entry
        self._save()
        return entry

    def get(self, pipeline: str, metric: str) -> Optional[BaselineEntry]:
        return self._data.get(pipeline, {}).get(metric)

    def list_entries(self) -> List[BaselineEntry]:
        return [e for metrics in self._data.values() for e in metrics.values()]

    def check_drift(
        self, pipeline: str, metric: str, current_value: float, threshold_pct: float = 10.0
    ) -> Optional[BaselineDrift]:
        entry = self.get(pipeline, metric)
        if entry is None:
            return None
        return BaselineDrift(
            pipeline=pipeline,
            metric=metric,
            baseline_value=entry.value,
            current_value=current_value,
            threshold_pct=threshold_pct,
        )

    def clear(self) -> None:
        self._data = {}
        self._save()
