"""Alert batching: collect multiple alert events and emit them as a single batch."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from pipewarden.runner import AlertEvent


@dataclass
class BatchRecord:
    pipeline: str
    events: List[AlertEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    flushed_at: Optional[datetime] = None

    @property
    def size(self) -> int:
        return len(self.events)

    @property
    def is_flushed(self) -> bool:
        return self.flushed_at is not None

    def __str__(self) -> str:
        status = "flushed" if self.is_flushed else "pending"
        return f"BatchRecord(pipeline={self.pipeline}, size={self.size}, status={status})"


@dataclass
class BatchPolicy:
    max_size: int = 10
    max_age_seconds: float = 60.0

    def __post_init__(self) -> None:
        if self.max_size < 1:
            raise ValueError("max_size must be >= 1")
        if self.max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be > 0")

    def should_flush(self, record: BatchRecord) -> bool:
        if record.size >= self.max_size:
            return True
        age = (datetime.now(timezone.utc) - record.created_at).total_seconds()
        return age >= self.max_age_seconds


class BatchManager:
    def __init__(self, policy: Optional[BatchPolicy] = None) -> None:
        self.policy = policy or BatchPolicy()
        self._batches: dict[str, BatchRecord] = {}

    def add(self, event: AlertEvent) -> Optional[BatchRecord]:
        pipeline = event.rule.pipeline
        if pipeline not in self._batches:
            self._batches[pipeline] = BatchRecord(pipeline=pipeline)
        record = self._batches[pipeline]
        record.events.append(event)
        if self.policy.should_flush(record):
            return self.flush(pipeline)
        return None

    def flush(self, pipeline: str) -> Optional[BatchRecord]:
        record = self._batches.pop(pipeline, None)
        if record is not None:
            record.flushed_at = datetime.now(timezone.utc)
        return record

    def flush_all(self) -> List[BatchRecord]:
        pipelines = list(self._batches.keys())
        return [r for p in pipelines if (r := self.flush(p)) is not None]

    def pending(self) -> List[BatchRecord]:
        return list(self._batches.values())
