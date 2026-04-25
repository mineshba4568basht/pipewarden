"""Tests for pipewarden.transformation."""
from __future__ import annotations

import math
import pytest

from pipewarden.transformation import (
    TransformationRule,
    TransformResult,
    batch_transform,
    transform,
)


# ---------------------------------------------------------------------------
# TransformationRule construction
# ---------------------------------------------------------------------------

class TestTransformationRuleConstruction:
    def test_defaults(self):
        rule = TransformationRule(name="r", fn="abs")
        assert rule.scale == 1.0
        assert rule.offset == 0.0

    def test_invalid_fn_raises(self):
        with pytest.raises(ValueError, match="Unknown transform function"):
            TransformationRule(name="r", fn="nonexistent")

    def test_zero_scale_raises(self):
        with pytest.raises(ValueError, match="scale must be non-zero"):
            TransformationRule(name="r", fn="abs", scale=0)

    def test_str_contains_name_and_fn(self):
        rule = TransformationRule(name="myrule", fn="sqrt")
        s = str(rule)
        assert "myrule" in s
        assert "sqrt" in s


# ---------------------------------------------------------------------------
# TransformationRule.apply
# ---------------------------------------------------------------------------

class TestTransformationRuleApply:
    def test_abs_positive(self):
        rule = TransformationRule(name="r", fn="abs")
        assert rule.apply(5.0) == 5.0

    def test_abs_negative(self):
        rule = TransformationRule(name="r", fn="abs")
        assert rule.apply(-3.0) == 3.0

    def test_negate(self):
        rule = TransformationRule(name="r", fn="negate")
        assert rule.apply(4.0) == -4.0

    def test_scale_applied_before_fn(self):
        # scale=2, offset=0, fn=abs => abs(value*2)
        rule = TransformationRule(name="r", fn="abs", scale=2.0)
        assert rule.apply(-3.0) == 6.0

    def test_offset_applied_before_fn(self):
        # scale=1, offset=10, fn=abs => abs(value+10)
        rule = TransformationRule(name="r", fn="abs", offset=10.0)
        assert rule.apply(-5.0) == 5.0

    def test_sqrt_positive(self):
        rule = TransformationRule(name="r", fn="sqrt")
        assert rule.apply(9.0) == pytest.approx(3.0)

    def test_sqrt_negative_returns_zero(self):
        rule = TransformationRule(name="r", fn="sqrt")
        assert rule.apply(-1.0) == 0.0

    def test_log10_positive(self):
        rule = TransformationRule(name="r", fn="log10")
        assert rule.apply(100.0) == pytest.approx(2.0)

    def test_log10_non_positive_returns_zero(self):
        rule = TransformationRule(name="r", fn="log10")
        assert rule.apply(0.0) == 0.0


# ---------------------------------------------------------------------------
# transform() helper
# ---------------------------------------------------------------------------

class TestTransformFunction:
    def test_returns_transform_result(self):
        rule = TransformationRule(name="t", fn="abs")
        result = transform(rule, -7.0)
        assert isinstance(result, TransformResult)

    def test_original_preserved(self):
        rule = TransformationRule(name="t", fn="abs")
        result = transform(rule, -7.0)
        assert result.original == -7.0

    def test_transformed_correct(self):
        rule = TransformationRule(name="t", fn="abs")
        result = transform(rule, -7.0)
        assert result.transformed == 7.0

    def test_changed_true_when_value_differs(self):
        rule = TransformationRule(name="t", fn="abs")
        result = transform(rule, -1.0)
        assert result.changed is True

    def test_changed_false_when_value_same(self):
        rule = TransformationRule(name="t", fn="abs")
        result = transform(rule, 5.0)
        assert result.changed is False

    def test_str_contains_rule_name(self):
        rule = TransformationRule(name="myrule", fn="abs")
        result = transform(rule, 3.0)
        assert "myrule" in str(result)

    def test_steps_populated(self):
        rule = TransformationRule(name="t", fn="abs")
        result = transform(rule, 1.0)
        assert len(result.steps) == 3


# ---------------------------------------------------------------------------
# batch_transform()
# ---------------------------------------------------------------------------

class TestBatchTransform:
    def test_returns_list_of_results(self):
        rule = TransformationRule(name="b", fn="abs")
        results = batch_transform(rule, [1.0, -2.0, 3.0])
        assert len(results) == 3

    def test_empty_input_returns_empty(self):
        rule = TransformationRule(name="b", fn="abs")
        assert batch_transform(rule, []) == []

    def test_each_result_correct(self):
        rule = TransformationRule(name="b", fn="negate")
        results = batch_transform(rule, [1.0, 2.0, 3.0])
        assert [r.transformed for r in results] == [-1.0, -2.0, -3.0]
