"""Tests for pipewarden.validation and pipewarden.validation_cli."""
from __future__ import annotations

import argparse
import pytest

from pipewarden.validation import (
    ValidationRule,
    ValidationViolation,
    ValidationResult,
    validate,
)
from pipewarden.validation_cli import build_validation_parser, handle_validation


# ---------------------------------------------------------------------------
# ValidationRule
# ---------------------------------------------------------------------------

class TestValidationRule:
    def test_valid_rule_constructed(self):
        r = ValidationRule(field="count", rule="min", value=0)
        assert r.field == "count"
        assert r.rule == "min"
        assert r.value == 0

    def test_invalid_rule_raises(self):
        with pytest.raises(ValueError, match="Unknown rule"):
            ValidationRule(field="x", rule="unknown")

    def test_str_contains_field_and_rule(self):
        r = ValidationRule(field="rows", rule="max", value=1000)
        assert "rows" in str(r)
        assert "max" in str(r)


# ---------------------------------------------------------------------------
# ValidationViolation
# ---------------------------------------------------------------------------

class TestValidationViolation:
    def test_str_contains_field_and_rule(self):
        v = ValidationViolation(field="name", rule="required", message="Field 'name' is required.")
        assert "name" in str(v)
        assert "required" in str(v)


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

class TestValidationResult:
    def test_passed_when_no_violations(self):
        r = ValidationResult(pipeline="pipe")
        assert r.passed is True

    def test_failed_when_violations_present(self):
        v = ValidationViolation(field="x", rule="required", message="missing")
        r = ValidationResult(pipeline="pipe", violations=[v])
        assert r.passed is False

    def test_str_contains_pipeline(self):
        r = ValidationResult(pipeline="my_pipeline")
        assert "my_pipeline" in str(r)

    def test_str_shows_fail_count(self):
        v = ValidationViolation(field="x", rule="required", message="missing")
        r = ValidationResult(pipeline="p", violations=[v])
        assert "1 violation" in str(r)


# ---------------------------------------------------------------------------
# validate()
# ---------------------------------------------------------------------------

class TestValidateFunction:
    def test_required_passes(self):
        rules = [ValidationRule(field="name", rule="required")]
        result = validate("p", {"name": "alice"}, rules)
        assert result.passed

    def test_required_fails_on_missing(self):
        rules = [ValidationRule(field="name", rule="required")]
        result = validate("p", {}, rules)
        assert not result.passed
        assert result.violations[0].field == "name"

    def test_required_fails_on_empty_string(self):
        rules = [ValidationRule(field="name", rule="required")]
        result = validate("p", {"name": ""}, rules)
        assert not result.passed

    def test_min_passes(self):
        rules = [ValidationRule(field="count", rule="min", value=0)]
        result = validate("p", {"count": 5}, rules)
        assert result.passed

    def test_min_fails(self):
        rules = [ValidationRule(field="count", rule="min", value=10)]
        result = validate("p", {"count": 3}, rules)
        assert not result.passed

    def test_max_passes(self):
        rules = [ValidationRule(field="count", rule="max", value=100)]
        result = validate("p", {"count": 50}, rules)
        assert result.passed

    def test_max_fails(self):
        rules = [ValidationRule(field="count", rule="max", value=10)]
        result = validate("p", {"count": 99}, rules)
        assert not result.passed

    def test_type_passes(self):
        rules = [ValidationRule(field="rows", rule="type", value="int")]
        result = validate("p", {"rows": 42}, rules)
        assert result.passed

    def test_type_fails(self):
        rules = [ValidationRule(field="rows", rule="type", value="int")]
        result = validate("p", {"rows": "not-an-int"}, rules)
        assert not result.passed

    def test_regex_passes(self):
        rules = [ValidationRule(field="code", rule="regex", value=r"[A-Z]{3}")]
        result = validate("p", {"code": "ABC"}, rules)
        assert result.passed

    def test_regex_fails(self):
        rules = [ValidationRule(field="code", rule="regex", value=r"[A-Z]{3}")]
        result = validate("p", {"code": "abc"}, rules)
        assert not result.passed

    def test_multiple_violations_collected(self):
        rules = [
            ValidationRule(field="name", rule="required"),
            ValidationRule(field="count", rule="min", value=1),
        ]
        result = validate("p", {"count": 0}, rules)
        assert len(result.violations) == 2

    def test_none_value_skips_min_max(self):
        rules = [ValidationRule(field="x", rule="min", value=0)]
        result = validate("p", {"x": None}, rules)
        assert result.passed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def validation_parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    build_validation_parser(sub)
    return p


class TestBuildValidationParser:
    def test_validation_subcommand_registered(self, validation_parser):
        args = validation_parser.parse_args(["validation", "info"])
        assert args.cmd == "validation"

    def test_run_stores_pipeline(self, validation_parser):
        args = validation_parser.parse_args(
            ["validation", "run", "--pipeline", "my_pipe", "--record", '{"x": 1}']
        )
        assert args.pipeline == "my_pipe"

    def test_run_default_pipeline(self, validation_parser):
        args = validation_parser.parse_args(
            ["validation", "run", "--record", '{"x": 1}']
        )
        assert args.pipeline == "default"

    def test_run_collects_rules(self, validation_parser):
        args = validation_parser.parse_args(
            [
                "validation", "run",
                "--record", '{"x": 5}',
                "--rule", "x:min:0",
                "--rule", "x:max:10",
            ]
        )
        assert len(args.rules) == 2

    def test_handle_validation_run_pass(self, capsys, validation_parser):
        args = validation_parser.parse_args(
            ["validation", "run", "--record", '{"count": 5}', "--rule", "count:min:0"]
        )
        handle_validation(args)
        out = capsys.readouterr().out
        assert "PASS" in out

    def test_handle_validation_run_fail(self, capsys, validation_parser):
        args = validation_parser.parse_args(
            ["validation", "run", "--record", '{"count": -1}', "--rule", "count:min:0"]
        )
        handle_validation(args)
        out = capsys.readouterr().out
        assert "FAIL" in out

    def test_handle_validation_info(self, capsys, validation_parser):
        args = validation_parser.parse_args(["validation", "info"])
        handle_validation(args)
        out = capsys.readouterr().out
        assert "required" in out
        assert "regex" in out

    def test_handle_validation_invalid_json(self, capsys, validation_parser):
        args = validation_parser.parse_args(
            ["validation", "run", "--record", "not-json"]
        )
        handle_validation(args)
        out = capsys.readouterr().out
        assert "Invalid JSON" in out
