"""Tests for pipewarden.normalization."""
import pytest

from pipewarden.normalization import (
    NormalizationRule,
    NormalizeResult,
    batch_normalize,
    normalize,
)


# ---------------------------------------------------------------------------
# NormalizationRule construction
# ---------------------------------------------------------------------------

class TestNormalizationRuleConstruction:
    def test_default_strategy_is_minmax(self):
        rule = NormalizationRule(metric="row_count")
        assert rule.strategy == "minmax"

    def test_invalid_strategy_raises(self):
        with pytest.raises(ValueError, match="strategy must be one of"):
            NormalizationRule(metric="x", strategy="log")

    def test_minmax_equal_bounds_raises(self):
        with pytest.raises(ValueError, match="max_val must be greater than min_val"):
            NormalizationRule(metric="x", strategy="minmax", min_val=5.0, max_val=5.0)

    def test_str_contains_metric_and_strategy(self):
        rule = NormalizationRule(metric="latency", strategy="zscore")
        assert "latency" in str(rule)
        assert "zscore" in str(rule)


# ---------------------------------------------------------------------------
# NormalizeResult
# ---------------------------------------------------------------------------

class TestNormalizeResult:
    def test_str_contains_metric(self):
        r = NormalizeResult(metric="rows", raw=50.0, normalized=0.5, strategy="minmax")
        assert "rows" in str(r)

    def test_str_contains_normalized_value(self):
        r = NormalizeResult(metric="rows", raw=50.0, normalized=0.5, strategy="minmax")
        assert "0.5000" in str(r)


# ---------------------------------------------------------------------------
# normalize – minmax
# ---------------------------------------------------------------------------

class TestNormalizeMinmax:
    def test_midpoint_returns_half(self):
        rule = NormalizationRule(metric="x", min_val=0.0, max_val=100.0)
        result = normalize(rule, 50.0)
        assert result.normalized == pytest.approx(0.5)

    def test_min_boundary_returns_zero(self):
        rule = NormalizationRule(metric="x", min_val=0.0, max_val=100.0)
        assert normalize(rule, 0.0).normalized == pytest.approx(0.0)

    def test_max_boundary_returns_one(self):
        rule = NormalizationRule(metric="x", min_val=0.0, max_val=100.0)
        assert normalize(rule, 100.0).normalized == pytest.approx(1.0)

    def test_strategy_recorded_in_result(self):
        rule = NormalizationRule(metric="x")
        assert normalize(rule, 10.0).strategy == "minmax"


# ---------------------------------------------------------------------------
# normalize – zscore
# ---------------------------------------------------------------------------

class TestNormalizeZscore:
    def test_no_history_returns_zero(self):
        rule = NormalizationRule(metric="x", strategy="zscore")
        assert normalize(rule, 42.0).normalized == pytest.approx(0.0)

    def test_single_history_returns_zero(self):
        rule = NormalizationRule(metric="x", strategy="zscore")
        assert normalize(rule, 42.0, history=[42.0]).normalized == pytest.approx(0.0)

    def test_value_at_mean_returns_zero(self):
        rule = NormalizationRule(metric="x", strategy="zscore")
        history = [10.0, 20.0, 30.0]
        result = normalize(rule, 20.0, history=history)
        assert result.normalized == pytest.approx(0.0, abs=1e-9)

    def test_outlier_has_high_zscore(self):
        rule = NormalizationRule(metric="x", strategy="zscore")
        history = [10.0] * 9 + [10.0]
        result = normalize(rule, 100.0, history=history)
        assert abs(result.normalized) > 1.0


# ---------------------------------------------------------------------------
# normalize – clamp
# ---------------------------------------------------------------------------

class TestNormalizeClamp:
    def test_value_below_low_clamped(self):
        rule = NormalizationRule(metric="x", strategy="clamp", clamp_low=0.0, clamp_high=10.0)
        assert normalize(rule, -5.0).normalized == pytest.approx(0.0)

    def test_value_above_high_clamped(self):
        rule = NormalizationRule(metric="x", strategy="clamp", clamp_low=0.0, clamp_high=10.0)
        assert normalize(rule, 99.0).normalized == pytest.approx(10.0)

    def test_value_within_range_unchanged(self):
        rule = NormalizationRule(metric="x", strategy="clamp", clamp_low=0.0, clamp_high=10.0)
        assert normalize(rule, 5.0).normalized == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# batch_normalize
# ---------------------------------------------------------------------------

class TestBatchNormalize:
    def test_returns_only_matching_metrics(self):
        rules = [NormalizationRule(metric="a"), NormalizationRule(metric="b")]
        results = batch_normalize(rules, {"a": 50.0, "c": 10.0})
        assert len(results) == 1
        assert results[0].metric == "a"

    def test_all_metrics_normalized(self):
        rules = [
            NormalizationRule(metric="a", min_val=0.0, max_val=100.0),
            NormalizationRule(metric="b", min_val=0.0, max_val=10.0),
        ]
        results = batch_normalize(rules, {"a": 50.0, "b": 5.0})
        assert len(results) == 2
        assert all(r.normalized == pytest.approx(0.5) for r in results)

    def test_empty_values_returns_empty(self):
        rules = [NormalizationRule(metric="a")]
        assert batch_normalize(rules, {}) == []
