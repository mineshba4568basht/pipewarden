"""Tests for pipewarden.redaction."""
from __future__ import annotations

import pytest

from pipewarden.redaction import RedactionPolicy, _REDACTED, _DEFAULT_PATTERNS
from pipewarden.runner import AlertEvent
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.config import AlertRule


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_rule(name: str = "test_rule") -> AlertRule:
    return AlertRule(name=name, pipeline="pipe", check="row_count", threshold=10)


def _make_result(passed: bool = False) -> CheckResult:
    return CheckResult(
        check_name="row_count",
        status=CheckStatus.PASS if passed else CheckStatus.FAIL,
        value=0,
        threshold=10,
    )


def _make_event(metadata: dict | None = None) -> AlertEvent:
    return AlertEvent(
        rule=_make_rule(),
        result=_make_result(),
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# RedactionPolicy construction
# ---------------------------------------------------------------------------

class TestRedactionPolicyConstruction:
    def test_defaults_use_common_patterns(self):
        policy = RedactionPolicy()
        assert "password" in policy.patterns
        assert "token" in policy.patterns

    def test_empty_patterns_raises(self):
        with pytest.raises(ValueError, match="patterns must not be empty"):
            RedactionPolicy(patterns=[])

    def test_custom_patterns_accepted(self):
        policy = RedactionPolicy(patterns=[r"ssn", r"dob"])
        assert policy.patterns == [r"ssn", r"dob"]


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------

class TestIsSensitive:
    def test_password_key_is_sensitive(self):
        policy = RedactionPolicy()
        assert policy.is_sensitive("password") is True

    def test_case_insensitive_match(self):
        policy = RedactionPolicy()
        assert policy.is_sensitive("API_KEY") is True

    def test_non_sensitive_key(self):
        policy = RedactionPolicy()
        assert policy.is_sensitive("row_count") is False

    def test_partial_match_in_key(self):
        policy = RedactionPolicy()
        assert policy.is_sensitive("user_token_value") is True


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------

class TestApply:
    def test_sensitive_values_replaced(self):
        policy = RedactionPolicy()
        result = policy.apply({"password": "s3cr3t", "row_count": 42})
        assert result["password"] == _REDACTED
        assert result["row_count"] == 42

    def test_empty_metadata_returns_empty(self):
        policy = RedactionPolicy()
        assert policy.apply({}) == {}

    def test_original_not_mutated(self):
        policy = RedactionPolicy()
        original = {"api_key": "abc123", "count": 5}
        policy.apply(original)
        assert original["api_key"] == "abc123"


# ---------------------------------------------------------------------------
# redact_event
# ---------------------------------------------------------------------------

class TestRedactEvent:
    def test_returns_new_event_with_clean_metadata(self):
        policy = RedactionPolicy()
        event = _make_event(metadata={"secret": "xyz", "pipeline": "my_pipe"})
        clean = policy.redact_event(event)
        assert clean.metadata["secret"] == _REDACTED
        assert clean.metadata["pipeline"] == "my_pipe"

    def test_original_event_unchanged(self):
        policy = RedactionPolicy()
        event = _make_event(metadata={"token": "abc"})
        policy.redact_event(event)
        assert event.metadata["token"] == "abc"

    def test_rule_and_result_preserved(self):
        policy = RedactionPolicy()
        event = _make_event()
        clean = policy.redact_event(event)
        assert clean.rule is event.rule
        assert clean.result is event.result
