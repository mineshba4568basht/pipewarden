"""Tests for pipewarden.baseline."""
from __future__ import annotations

import pytest

from pipewarden.baseline import BaselineDrift, BaselineEntry, BaselineStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(tmp_path):
    return BaselineStore(path=str(tmp_path / "baselines.json"))


# ---------------------------------------------------------------------------
# BaselineEntry
# ---------------------------------------------------------------------------

class TestBaselineEntry:
    def test_str_contains_pipeline_and_metric(self):
        e = BaselineEntry(pipeline="orders", metric="row_count", value=500.0)
        assert "orders" in str(e)
        assert "row_count" in str(e)
        assert "500.0" in str(e)

    def test_captured_at_set_automatically(self):
        e = BaselineEntry(pipeline="p", metric="m", value=1.0)
        assert e.captured_at  # non-empty


# ---------------------------------------------------------------------------
# BaselineDrift
# ---------------------------------------------------------------------------

class TestBaselineDrift:
    def _drift(self, baseline, current, threshold=10.0):
        return BaselineDrift(
            pipeline="p", metric="m",
            baseline_value=baseline,
            current_value=current,
            threshold_pct=threshold,
        )

    def test_delta(self):
        assert self._drift(100.0, 115.0).delta == pytest.approx(15.0)

    def test_pct_change(self):
        assert self._drift(100.0, 115.0).pct_change == pytest.approx(15.0)

    def test_pct_change_zero_baseline(self):
        assert self._drift(0.0, 5.0).pct_change is None

    def test_is_drifted_true(self):
        assert self._drift(100.0, 120.0, threshold=10.0).is_drifted is True

    def test_is_drifted_false(self):
        assert self._drift(100.0, 105.0, threshold=10.0).is_drifted is False

    def test_str_contains_status_drifted(self):
        assert "DRIFTED" in str(self._drift(100.0, 200.0))

    def test_str_contains_status_ok(self):
        assert "OK" in str(self._drift(100.0, 101.0))


# ---------------------------------------------------------------------------
# BaselineStore
# ---------------------------------------------------------------------------

class TestBaselineStore:
    def test_set_and_get(self, store):
        store.set("pipe", "rows", 1000.0)
        entry = store.get("pipe", "rows")
        assert entry is not None
        assert entry.value == 1000.0

    def test_get_missing_returns_none(self, store):
        assert store.get("missing", "metric") is None

    def test_list_entries(self, store):
        store.set("a", "m1", 1.0)
        store.set("b", "m2", 2.0)
        assert len(store.list_entries()) == 2

    def test_persistence(self, tmp_path):
        path = str(tmp_path / "bl.json")
        s1 = BaselineStore(path=path)
        s1.set("pipe", "rows", 42.0)
        s2 = BaselineStore(path=path)
        assert s2.get("pipe", "rows").value == 42.0

    def test_clear(self, store):
        store.set("p", "m", 1.0)
        store.clear()
        assert store.list_entries() == []

    def test_check_drift_no_baseline(self, store):
        assert store.check_drift("p", "m", 100.0) is None

    def test_check_drift_returns_drift(self, store):
        store.set("p", "m", 100.0)
        drift = store.check_drift("p", "m", 150.0, threshold_pct=10.0)
        assert drift is not None
        assert drift.is_drifted is True
