"""Tests for pipewarden.runner module."""

import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.config import AlertRule, PipewardenConfig
from pipewarden.runner import AlertEvent, CheckRunner, RunReport


@pytest.fixture
def simple_config():
    rules = [
        AlertRule(
            name="row_count_alert",
            check_name="row_count",
            on_status=["fail"],
            severity="critical",
            message="Row count check failed!",
        ),
        AlertRule(
            name="null_rate_warn",
            check_name="null_rate",
            on_status=["fail", "error"],
            severity="warning",
        ),
    ]
    return PipewardenConfig(pipeline_name="test_pipeline", alert_rules=rules)


@pytest.fixture
default_runner(simple_config):
    return CheckRunner(config=simple_config)


@pytest.fixture
def runner(simple_config):
    return CheckRunner(config=simple_config)


class TestRunReport:
    def test_passed_when_all_pass(self):
        results = [
            CheckResult(name="a", status=CheckStatus.PASS, message="ok"),
            CheckResult(name="b", status=CheckStatus.PASS, message="ok"),
        ]
        report = RunReport(results=results)
        assert report.passed is True

    def test_failed_when_any_fail(self):
        results = [
            CheckResult(name="a", status=CheckStatus.PASS, message="ok"),
            CheckResult(name="b", status=CheckStatus.FAIL, message="bad"),
        ]
        report = RunReport(results=results)
        assert report.passed is False
        assert len(report.failed_checks) == 1

    def test_summary_contains_status(self):
        results = [CheckResult(name="a", status=CheckStatus.PASS, message="ok")]
        report = RunReport(results=results)
        assert "PASSED" in report.summary()


class TestCheckRunner:
    def test_triggers_alert_on_fail(self, runner):
        results = [
            CheckResult(name="row_count", status=CheckStatus.FAIL, message="too few rows"),
        ]
        alerts = runner.evaluate_rules(results)
        assert len(alerts) == 1
        assert alerts[0].rule_name == "row_count_alert"
        assert alerts[0].severity == "critical"

    def test_no_alert_on_pass(self, runner):
        results = [
            CheckResult(name="row_count", status=CheckStatus.PASS, message="ok"),
        ]
        alerts = runner.evaluate_rules(results)
        assert len(alerts) == 0

    def test_skips_missing_check(self, runner, caplog):
        import logging
        with caplog.at_level(logging.WARNING):
            alerts = runner.evaluate_rules([])
        assert len(alerts) == 0
        assert "No check result found" in caplog.text

    def test_run_returns_report(self, runner):
        results = [
            CheckResult(name="row_count", status=CheckStatus.FAIL, message="bad"),
            CheckResult(name="null_rate", status=CheckStatus.PASS, message="ok"),
        ]
        report = runner.run(results)
        assert isinstance(report, RunReport)
        assert len(report.alerts) == 1
        assert not report.passed

    def test_alert_uses_custom_message(self, runner):
        results = [
            CheckResult(name="row_count", status=CheckStatus.FAIL, message="default msg"),
        ]
        alerts = runner.evaluate_rules(results)
        assert alerts[0].message == "Row count check failed!"
