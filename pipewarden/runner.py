"""Pipeline check runner — executes checks and evaluates alert rules."""

from dataclasses import dataclass, field
from typing import List, Optional
import logging

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.config import AlertRule, PipewardenConfig

logger = logging.getLogger(__name__)


@dataclass
class AlertEvent:
    rule_name: str
    severity: str
    message: str
    check_result: CheckResult

    def __str__(self) -> str:
        return f"ALERT [{self.severity.upper()}] {self.rule_name}: {self.message}"


@dataclass
class RunReport:
    results: List[CheckResult] = field(default_factory=list)
    alerts: List[AlertEvent] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failed_checks(self) -> List[CheckResult]:
        return [r for r in self.results if not r.passed]

    def summary(self) -> str:
        total = len(self.results)
        failed = len(self.failed_checks)
        alert_count = len(self.alerts)
        status = "PASSED" if self.passed else "FAILED"
        return (
            f"Run {status}: {total - failed}/{total} checks passed, "
            f"{alert_count} alert(s) triggered"
        )


class CheckRunner:
    """Runs a list of CheckResults against configured alert rules."""

    def __init__(self, config: PipewardenConfig) -> None:
        self.config = config

    def evaluate_rules(self, results: List[CheckResult]) -> List[AlertEvent]:
        """Evaluate alert rules against check results and return triggered alerts."""
        alerts: List[AlertEvent] = []
        results_by_name = {r.name: r for r in results}

        for rule in self.config.alert_rules:
            result = results_by_name.get(rule.check_name)
            if result is None:
                logger.warning("No check result found for rule '%s'", rule.check_name)
                continue
            if result.status.value in rule.on_status:
                alert = AlertEvent(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=rule.message or str(result),
                    check_result=result,
                )
                alerts.append(alert)
                logger.info("Alert triggered: %s", alert)

        return alerts

    def run(self, results: List[CheckResult]) -> RunReport:
        """Process check results and build a full run report."""
        alerts = self.evaluate_rules(results)
        report = RunReport(results=results, alerts=alerts)
        logger.info(report.summary())
        return report
