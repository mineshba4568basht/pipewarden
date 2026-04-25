"""Tests for pipewarden.tracing."""
from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest

from pipewarden.tracing import TraceContext, TraceSpan, new_trace


# ---------------------------------------------------------------------------
# TraceSpan
# ---------------------------------------------------------------------------

class TestTraceSpan:
    def _span(self, status: str = "ok") -> TraceSpan:
        s = TraceSpan(pipeline="orders", check="row_count", trace_id="abc123")
        s.finish(status)
        return s

    def test_span_id_generated(self):
        s = TraceSpan(pipeline="p", check="c", trace_id="t")
        assert len(s.span_id) == 16

    def test_started_at_set_automatically(self):
        s = TraceSpan(pipeline="p", check="c", trace_id="t")
        assert isinstance(s.started_at, datetime)

    def test_finish_sets_ended_at(self):
        s = TraceSpan(pipeline="p", check="c", trace_id="t")
        assert s.ended_at is None
        s.finish()
        assert s.ended_at is not None

    def test_finish_sets_status(self):
        s = TraceSpan(pipeline="p", check="c", trace_id="t")
        s.finish("error")
        assert s.status == "error"

    def test_duration_ms_none_before_finish(self):
        s = TraceSpan(pipeline="p", check="c", trace_id="t")
        assert s.duration_ms is None

    def test_duration_ms_non_negative_after_finish(self):
        s = self._span()
        assert s.duration_ms is not None
        assert s.duration_ms >= 0

    def test_str_contains_pipeline_and_check(self):
        s = self._span()
        assert "orders" in str(s)
        assert "row_count" in str(s)

    def test_str_contains_status(self):
        s = self._span("error")
        assert "error" in str(s)

    def test_str_inprogress_before_finish(self):
        s = TraceSpan(pipeline="p", check="c", trace_id="t")
        assert "in-progress" in str(s)


# ---------------------------------------------------------------------------
# TraceContext
# ---------------------------------------------------------------------------

class TestTraceContext:
    def _ctx(self) -> TraceContext:
        return new_trace()

    def test_trace_id_is_hex_string(self):
        ctx = self._ctx()
        int(ctx.trace_id, 16)  # should not raise

    def test_start_span_appends_to_spans(self):
        ctx = self._ctx()
        ctx.start_span("pipe", "check")
        assert len(ctx.spans) == 1

    def test_start_span_sets_trace_id(self):
        ctx = self._ctx()
        span = ctx.start_span("pipe", "check")
        assert span.trace_id == ctx.trace_id

    def test_root_span_has_no_parent(self):
        ctx = self._ctx()
        root = ctx.start_span("pipe", "root")
        child = ctx.start_span("pipe", "child", parent_span_id=root.span_id)
        assert ctx.root_span() is root

    def test_failed_spans_filters_errors(self):
        ctx = self._ctx()
        s1 = ctx.start_span("p", "c1")
        s1.finish("ok")
        s2 = ctx.start_span("p", "c2")
        s2.finish("error")
        assert ctx.failed_spans() == [s2]

    def test_str_contains_trace_id_prefix(self):
        ctx = self._ctx()
        assert ctx.trace_id[:8] in str(ctx)

    def test_new_trace_returns_trace_context(self):
        ctx = new_trace()
        assert isinstance(ctx, TraceContext)
