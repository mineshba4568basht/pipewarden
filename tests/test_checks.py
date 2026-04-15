"""Tests for pipewarden.checks module."""

import pytest
from pipewarden.checks import (
    CheckStatus,
    CheckResult,
    check_row_count,
    check_null_rate,
    check_freshness,
)


class TestCheckResult:
    def test_passed_property_true(self):
        result = CheckResult(name="test", status=CheckStatus.PASS, message="ok")
        assert result.passed is True

    def test_passed_property_false_on_fail(self):
        result = CheckResult(name="test", status=CheckStatus.FAIL, message="bad")
        assert result.passed is False

    def test_str_representation(self):
        result = CheckResult(name="my_check", status=CheckStatus.WARN, message="watch out")
        assert "WARN" in str(result)
        assert "my_check" in str(result)


class TestCheckRowCount:
    def test_passes_within_range(self):
        result = check_row_count(actual=500, min_count=100, max_count=1000)
        assert result.status == CheckStatus.PASS

    def test_fails_below_minimum(self):
        result = check_row_count(actual=50, min_count=100)
        assert result.status == CheckStatus.FAIL
        assert result.value == 50
        assert result.threshold == 100

    def test_fails_above_maximum(self):
        result = check_row_count(actual=2000, max_count=1000)
        assert result.status == CheckStatus.FAIL
        assert result.value == 2000

    def test_passes_no_bounds(self):
        result = check_row_count(actual=999999)
        assert result.status == CheckStatus.PASS

    def test_custom_name(self):
        result = check_row_count(actual=10, name="orders_count")
        assert result.name == "orders_count"


class TestCheckNullRate:
    def test_passes_below_threshold(self):
        result = check_null_rate(null_count=2, total_count=100, max_rate=0.05)
        assert result.status == CheckStatus.PASS
        assert pytest.approx(result.value, 0.001) == 0.02

    def test_fails_above_threshold(self):
        result = check_null_rate(null_count=10, total_count=100, max_rate=0.05)
        assert result.status == CheckStatus.FAIL

    def test_error_on_zero_total(self):
        result = check_null_rate(null_count=0, total_count=0)
        assert result.status == CheckStatus.ERROR

    def test_metadata_contains_column(self):
        result = check_null_rate(null_count=1, total_count=100, column="email")
        assert result.metadata["column"] == "email"


class TestCheckFreshness:
    def test_passes_fresh_data(self):
        result = check_freshness(age_seconds=300, max_age_seconds=3600)
        assert result.status == CheckStatus.PASS

    def test_fails_stale_data(self):
        result = check_freshness(age_seconds=7200, max_age_seconds=3600)
        assert result.status == CheckStatus.FAIL
        assert result.value == 7200
        assert result.threshold == 3600

    def test_exactly_at_threshold_passes(self):
        result = check_freshness(age_seconds=3600, max_age_seconds=3600)
        assert result.status == CheckStatus.PASS
