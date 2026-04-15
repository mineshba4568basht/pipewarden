"""Tests for pipewarden.summary module."""
import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.config import AlertRule, PipewardenConfig
from pipewarden.runner import AlertEvent, RunReport
from pipewarden.summary import SummaryLine, build_summary, _header


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rule(severity: str = "warning", operator: str = ">=", threshold: float = 10.0) -> AlertRule:
    return AlertRule(
        name="test_rule",
        check="row_count",
        operator=operator,
        threshold=threshold,
        severity=severity,
    )


def _make_event(passed: bool, metric_value: float = 50.0, severity: str = "warning") -> AlertEvent:
    status = CheckStatus.PASS if passed else CheckStatus.FAIL
    result = CheckResult(
        check_name="test_rule",
        status=status,
        metric_value=metric_value,
        message="ok" if passed else "fail",
    )
    rule = _make_rule(severity=severity)
    return AlertEvent(result=result, rule=rule)


@pytest.fixture
def passing_report() -> RunReport:
    config = PipewardenConfig(rules=[_make_rule()])
    events = [_make_event(passed=True)]
    return RunReport(config=config, alert_events=events)


@pytest.fixture
def failing_report() -> RunReport:
    config = PipewardenConfig(rules=[_make_rule(severity="critical")])
    events = [_make_event(passed=False, severity="critical")]
    return RunReport(config=config, alert_events=events)


# ---------------------------------------------------------------------------
# SummaryLine
# ---------------------------------------------------------------------------

class TestSummaryLine:
    def test_str_contains_check_name(self):
        line = SummaryLine("my_check", "PASS", "100", ">= 10.0", "warning")
        assert "my_check" in str(line)

    def test_str_contains_status(self):
        line = SummaryLine("my_check", "FAIL", "5", ">= 10.0", "critical")
        assert "FAIL" in str(line)

    def test_str_contains_severity(self):
        line = SummaryLine("my_check", "PASS", "100", ">= 10.0", "critical")
        assert "critical" in str(line)


# ---------------------------------------------------------------------------
# build_summary
# ---------------------------------------------------------------------------

class TestBuildSummary:
    def test_header_present(self, passing_report):
        summary = build_summary(passing_report)
        assert "Check" in summary
        assert "Status" in summary

    def test_overall_passed(self, passing_report):
        summary = build_summary(passing_report)
        assert "Overall result: PASSED" in summary

    def test_overall_failed(self, failing_report):
        summary = build_summary(failing_report)
        assert "Overall result: FAILED" in summary

    def test_counts_in_summary(self, failing_report):
        summary = build_summary(failing_report)
        assert "Total: 1" in summary
        assert "Failed: 1" in summary
        assert "Passed: 0" in summary

    def test_check_name_in_summary(self, passing_report):
        summary = build_summary(passing_report)
        assert "test_rule" in summary

    def test_metric_value_in_summary(self, passing_report):
        summary = build_summary(passing_report)
        assert "50.0" in summary

    def test_empty_events(self):
        config = PipewardenConfig(rules=[])
        report = RunReport(config=config, alert_events=[])
        summary = build_summary(report)
        assert "Total: 0" in summary
        assert "Overall result: PASSED" in summary
