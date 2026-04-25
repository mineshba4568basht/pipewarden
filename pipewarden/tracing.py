"""Distributed trace context propagation for pipeline checks."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class TraceSpan:
    pipeline: str
    check: str
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_span_id: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    status: str = "ok"  # ok | error
    tags: Dict[str, str] = field(default_factory=dict)

    def finish(self, status: str = "ok") -> None:
        self.ended_at = datetime.now(timezone.utc)
        self.status = status

    @property
    def duration_ms(self) -> Optional[float]:
        if self.ended_at is None:
            return None
        delta = self.ended_at - self.started_at
        return round(delta.total_seconds() * 1000, 3)

    def __str__(self) -> str:
        dur = f"{self.duration_ms}ms" if self.duration_ms is not None else "in-progress"
        return (
            f"TraceSpan(trace={self.trace_id[:8]} span={self.span_id} "
            f"pipeline={self.pipeline} check={self.check} "
            f"status={self.status} duration={dur})"
        )


@dataclass
class TraceContext:
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    spans: List[TraceSpan] = field(default_factory=list)

    def start_span(
        self,
        pipeline: str,
        check: str,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> TraceSpan:
        span = TraceSpan(
            pipeline=pipeline,
            check=check,
            trace_id=self.trace_id,
            parent_span_id=parent_span_id,
            tags=tags or {},
        )
        self.spans.append(span)
        return span

    def root_span(self) -> Optional[TraceSpan]:
        for s in self.spans:
            if s.parent_span_id is None:
                return s
        return None

    def failed_spans(self) -> List[TraceSpan]:
        return [s for s in self.spans if s.status == "error"]

    def __str__(self) -> str:
        return (
            f"TraceContext(id={self.trace_id[:8]} "
            f"spans={len(self.spans)} failed={len(self.failed_spans())})"
        )


def new_trace() -> TraceContext:
    """Create a fresh TraceContext with a unique trace ID."""
    return TraceContext()
