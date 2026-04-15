"""Tests for pipewarden.baseline_cli."""
from __future__ import annotations

import argparse
import pytest

from pipewarden.baseline import BaselineStore
from pipewarden.baseline_cli import build_baseline_parser, handle_baseline


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def baseline_parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_baseline_parser(sub)
    return root


@pytest.fixture()
def store(tmp_path):
    return BaselineStore(path=str(tmp_path / "baselines.json"))


# ---------------------------------------------------------------------------
# Parser structure
# ---------------------------------------------------------------------------

class TestBuildBaselineParser:
    def test_baseline_subcommand_registered(self, baseline_parser):
        args = baseline_parser.parse_args(["baseline", "list"])
        assert args.command == "baseline"

    def test_set_stores_pipeline_metric_value(self, baseline_parser):
        args = baseline_parser.parse_args(["baseline", "set", "orders", "rows", "500"])
        assert args.pipeline == "orders"
        assert args.metric == "rows"
        assert args.value == 500.0

    def test_drift_default_threshold(self, baseline_parser):
        args = baseline_parser.parse_args(["baseline", "drift", "p", "m", "120"])
        assert args.threshold == 10.0

    def test_drift_custom_threshold(self, baseline_parser):
        args = baseline_parser.parse_args(["baseline", "drift", "p", "m", "120", "--threshold", "5"])
        assert args.threshold == 5.0


# ---------------------------------------------------------------------------
# handle_baseline
# ---------------------------------------------------------------------------

class TestHandleBaseline:
    def _args(self, baseline_parser, argv):
        return baseline_parser.parse_args(["baseline"] + argv)

    def test_set_returns_0(self, baseline_parser, store):
        args = self._args(baseline_parser, ["set", "p", "m", "100"])
        assert handle_baseline(args, store) == 0

    def test_get_existing_returns_0(self, baseline_parser, store):
        store.set("p", "m", 100.0)
        args = self._args(baseline_parser, ["get", "p", "m"])
        assert handle_baseline(args, store) == 0

    def test_get_missing_returns_1(self, baseline_parser, store):
        args = self._args(baseline_parser, ["get", "missing", "metric"])
        assert handle_baseline(args, store) == 1

    def test_list_returns_0(self, baseline_parser, store):
        args = self._args(baseline_parser, ["list"])
        assert handle_baseline(args, store) == 0

    def test_drift_no_baseline_returns_1(self, baseline_parser, store):
        args = self._args(baseline_parser, ["drift", "p", "m", "150"])
        assert handle_baseline(args, store) == 1

    def test_drift_drifted_returns_1(self, baseline_parser, store):
        store.set("p", "m", 100.0)
        args = self._args(baseline_parser, ["drift", "p", "m", "200"])
        assert handle_baseline(args, store) == 1

    def test_drift_ok_returns_0(self, baseline_parser, store):
        store.set("p", "m", 100.0)
        args = self._args(baseline_parser, ["drift", "p", "m", "102"])
        assert handle_baseline(args, store) == 0

    def test_clear_returns_0(self, baseline_parser, store):
        args = self._args(baseline_parser, ["clear"])
        assert handle_baseline(args, store) == 0
