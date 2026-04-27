"""Tests for pipewarden.offsetting."""
from __future__ import annotations

import pytest
from pipewarden.offsetting import OffsetDelta, OffsetEntry, OffsetStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store() -> OffsetStore:
    return OffsetStore()


# ---------------------------------------------------------------------------
# OffsetEntry
# ---------------------------------------------------------------------------

class TestOffsetEntry:
    def test_str_contains_pipeline_and_metric(self):
        e = OffsetEntry(pipeline="sales", metric="row_count", value=42.0)
        assert "sales" in str(e)
        assert "row_count" in str(e)

    def test_str_contains_value(self):
        e = OffsetEntry(pipeline="sales", metric="row_count", value=42.0)
        assert "42.0000" in str(e)

    def test_recorded_at_set_automatically(self):
        e = OffsetEntry(pipeline="p", metric="m", value=1.0)
        assert e.recorded_at is not None


# ---------------------------------------------------------------------------
# OffsetDelta
# ---------------------------------------------------------------------------

class TestOffsetDelta:
    def test_delta_positive(self):
        d = OffsetDelta(pipeline="p", metric="m", previous=10.0, current=15.0)
        assert d.delta == pytest.approx(5.0)

    def test_delta_negative(self):
        d = OffsetDelta(pipeline="p", metric="m", previous=10.0, current=7.0)
        assert d.delta == pytest.approx(-3.0)

    def test_pct_change_correct(self):
        d = OffsetDelta(pipeline="p", metric="m", previous=100.0, current=110.0)
        assert d.pct_change == pytest.approx(10.0)

    def test_pct_change_zero_previous(self):
        d = OffsetDelta(pipeline="p", metric="m", previous=0.0, current=5.0)
        assert d.pct_change is None

    def test_str_contains_delta(self):
        d = OffsetDelta(pipeline="p", metric="m", previous=10.0, current=12.0)
        assert "+2.0000" in str(d)

    def test_str_contains_na_when_previous_zero(self):
        d = OffsetDelta(pipeline="p", metric="m", previous=0.0, current=5.0)
        assert "n/a" in str(d)


# ---------------------------------------------------------------------------
# OffsetStore
# ---------------------------------------------------------------------------

class TestOffsetStore:
    def test_record_returns_entry(self, store):
        entry = store.record("pipe", "rows", 100.0)
        assert isinstance(entry, OffsetEntry)
        assert entry.value == 100.0

    def test_latest_returns_most_recent(self, store):
        store.record("pipe", "rows", 50.0)
        store.record("pipe", "rows", 75.0)
        latest = store.latest("pipe", "rows")
        assert latest is not None
        assert latest.value == 75.0

    def test_latest_returns_none_when_empty(self, store):
        assert store.latest("pipe", "rows") is None

    def test_diff_returns_delta(self, store):
        store.record("pipe", "rows", 100.0)
        delta = store.diff("pipe", "rows", 120.0)
        assert delta is not None
        assert delta.delta == pytest.approx(20.0)

    def test_diff_returns_none_with_no_history(self, store):
        assert store.diff("pipe", "rows", 50.0) is None

    def test_list_entries_respects_limit(self, store):
        for i in range(10):
            store.record("pipe", "rows", float(i))
        entries = store.list_entries(limit=3)
        assert len(entries) == 3

    def test_list_entries_filters_by_pipeline(self, store):
        store.record("pipe_a", "rows", 1.0)
        store.record("pipe_b", "rows", 2.0)
        entries = store.list_entries(pipeline="pipe_a")
        assert all(e.pipeline == "pipe_a" for e in entries)

    def test_clear_removes_all_entries(self, store):
        store.record("pipe", "rows", 1.0)
        store.record("pipe", "rows", 2.0)
        removed = store.clear()
        assert removed == 2
        assert store.list_entries() == []
