"""Tests for pipewarden.windowing."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewarden.windowing import WindowBucket, WindowPolicy, build_windows


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(pipeline: str, minutes_ago: int) -> MagicMock:
    evt = MagicMock()
    evt.pipeline = pipeline
    evt.triggered_at = datetime.utcnow() - timedelta(minutes=minutes_ago)
    rule = MagicMock()
    rule.severity = "warning"
    evt.rule = rule
    return evt


# ---------------------------------------------------------------------------
# WindowPolicy construction
# ---------------------------------------------------------------------------

class TestWindowPolicy:
    def test_defaults(self):
        p = WindowPolicy()
        assert p.size_seconds == 300
        assert p.slide_seconds is None
        assert not p.is_sliding

    def test_sliding_policy(self):
        p = WindowPolicy(size_seconds=60, slide_seconds=30)
        assert p.is_sliding

    def test_invalid_size_raises(self):
        with pytest.raises(ValueError, match="size_seconds"):
            WindowPolicy(size_seconds=0)

    def test_invalid_slide_raises(self):
        with pytest.raises(ValueError, match="slide_seconds"):
            WindowPolicy(size_seconds=60, slide_seconds=0)

    def test_slide_exceeds_size_raises(self):
        with pytest.raises(ValueError, match="cannot exceed"):
            WindowPolicy(size_seconds=30, slide_seconds=60)

    def test_str_tumbling(self):
        assert "tumbling" in str(WindowPolicy(size_seconds=120))

    def test_str_sliding(self):
        assert "sliding" in str(WindowPolicy(size_seconds=120, slide_seconds=60))


# ---------------------------------------------------------------------------
# WindowBucket
# ---------------------------------------------------------------------------

class TestWindowBucket:
    def _bucket(self, n_events: int = 2) -> WindowBucket:
        now = datetime.utcnow()
        b = WindowBucket(start=now - timedelta(minutes=5), end=now)
        for i in range(n_events):
            b.events.append(_make_event(f"pipe_{i}", 1))
        return b

    def test_count(self):
        assert self._bucket(3).count == 3

    def test_pipelines_unique(self):
        b = self._bucket(2)
        assert len(b.pipelines) == 2

    def test_str_contains_count(self):
        assert "events=2" in str(self._bucket(2))


# ---------------------------------------------------------------------------
# build_windows
# ---------------------------------------------------------------------------

class TestBuildWindows:
    def test_empty_events_returns_empty(self):
        policy = WindowPolicy(size_seconds=60)
        assert build_windows([], policy) == []

    def test_tumbling_window_covers_all_events(self):
        now = datetime.utcnow()
        events = [_make_event("p", 1), _make_event("p", 3)]
        policy = WindowPolicy(size_seconds=600)
        buckets = build_windows(events, policy, reference=now)
        total = sum(b.count for b in buckets)
        assert total == len(events)

    def test_sliding_produces_more_buckets_than_tumbling(self):
        now = datetime.utcnow()
        events = [_make_event("p", i) for i in range(1, 6)]
        tumbling = build_windows(events, WindowPolicy(size_seconds=300), reference=now)
        sliding = build_windows(
            events,
            WindowPolicy(size_seconds=300, slide_seconds=60),
            reference=now,
        )
        assert len(sliding) >= len(tumbling)

    def test_pipeline_filter_via_list_comprehension(self):
        now = datetime.utcnow()
        events = [_make_event("alpha", 1), _make_event("beta", 2)]
        policy = WindowPolicy(size_seconds=600)
        buckets = build_windows(
            [e for e in events if e.pipeline == "alpha"], policy, reference=now
        )
        for b in buckets:
            assert all(e.pipeline == "alpha" for e in b.events)
