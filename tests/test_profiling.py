"""Tests for pipewarden.profiling."""
from __future__ import annotations

import pytest
from pipewarden.profiling import ProfileSample, ProfileReport, ProfilingStore


# ---------------------------------------------------------------------------
# ProfileSample
# ---------------------------------------------------------------------------

class TestProfileSample:
    def test_str_contains_pipeline_and_check(self):
        s = ProfileSample(pipeline="etl", check="row_count", duration_ms=42.5)
        assert "etl" in str(s)
        assert "row_count" in str(s)

    def test_str_contains_duration(self):
        s = ProfileSample(pipeline="etl", check="row_count", duration_ms=123.0)
        assert "123.0" in str(s)

    def test_recorded_at_set_automatically(self):
        s = ProfileSample(pipeline="p", check="c", duration_ms=1.0)
        assert s.recorded_at is not None


# ---------------------------------------------------------------------------
# ProfileReport
# ---------------------------------------------------------------------------

class TestProfileReport:
    def _report(self, durations):
        return ProfileReport(pipeline="pipe", check="chk", samples=durations)

    def test_count(self):
        r = self._report([10.0, 20.0, 30.0])
        assert r.count == 3

    def test_mean(self):
        r = self._report([10.0, 20.0, 30.0])
        assert r.mean_ms == pytest.approx(20.0)

    def test_p95_single_sample(self):
        r = self._report([50.0])
        assert r.p95_ms == pytest.approx(50.0)

    def test_p95_multiple_samples(self):
        r = self._report(list(range(1, 101)))
        assert r.p95_ms is not None
        assert r.p95_ms >= 95.0

    def test_stdev_none_for_single(self):
        r = self._report([10.0])
        assert r.stdev_ms is None

    def test_stdev_computed_for_multiple(self):
        r = self._report([10.0, 20.0])
        assert r.stdev_ms is not None
        assert r.stdev_ms > 0

    def test_empty_samples_mean_none(self):
        r = self._report([])
        assert r.mean_ms is None

    def test_empty_samples_str(self):
        r = self._report([])
        assert "no samples" in str(r)

    def test_str_contains_stats(self):
        r = self._report([10.0, 20.0, 30.0])
        s = str(r)
        assert "mean=" in s
        assert "p95=" in s
        assert "n=3" in s


# ---------------------------------------------------------------------------
# ProfilingStore
# ---------------------------------------------------------------------------

class TestProfilingStore:
    def test_record_returns_sample(self):
        store = ProfilingStore()
        sample = store.record("etl", "row_count", 55.0)
        assert isinstance(sample, ProfileSample)
        assert sample.duration_ms == 55.0

    def test_all_samples_empty(self):
        store = ProfilingStore()
        assert store.all_samples() == []

    def test_all_samples_respects_limit(self):
        store = ProfilingStore()
        for i in range(10):
            store.record("p", "c", float(i))
        assert len(store.all_samples(limit=5)) == 5

    def test_report_filters_by_pipeline_and_check(self):
        store = ProfilingStore()
        store.record("p1", "c1", 10.0)
        store.record("p1", "c2", 20.0)
        store.record("p2", "c1", 30.0)
        report = store.report("p1", "c1")
        assert report.count == 1
        assert report.mean_ms == pytest.approx(10.0)

    def test_clear_all(self):
        store = ProfilingStore()
        store.record("p", "c", 1.0)
        store.record("p", "c", 2.0)
        removed = store.clear()
        assert removed == 2
        assert store.all_samples() == []

    def test_clear_by_pipeline(self):
        store = ProfilingStore()
        store.record("p1", "c", 1.0)
        store.record("p2", "c", 2.0)
        removed = store.clear(pipeline="p1")
        assert removed == 1
        remaining = store.all_samples()
        assert all(s.pipeline == "p2" for s in remaining)
