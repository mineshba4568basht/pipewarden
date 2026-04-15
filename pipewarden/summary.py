"""Summary report formatting for PipeWarden run results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from pipewarden.runner import RunReport, AlertEvent


@dataclass
class SummaryLine:
    """A single formatted line in a summary table."""
    check_name: str
    status: str
    metric: str
    threshold: str
    severity: str

    def __str__(self) -> str:
        return (
            f"{self.check_name:<30} {self.status:<8} "
            f"{self.metric:<15} {self.threshold:<15} {self.severity}"
        )


def _header() -> str:
    return (
        f"{'Check':<30} {'Status':<8} "
        f"{'Metric':<15} {'Threshold':<15} Severity\n"
        + "-" * 80
    )


def build_summary(report: RunReport) -> str:
    """Return a formatted multi-line summary string for a RunReport."""
    lines: List[str] = [_header()]

    for event in report.alert_events:
        result = event.result
        rule = event.rule
        status = "PASS" if result.passed else "FAIL"
        metric_val = str(result.metric_value) if result.metric_value is not None else "N/A"
        threshold_val = (
            f"{rule.operator} {rule.threshold}" if rule else "N/A"
        )
        severity = rule.severity if rule else "info"
        line = SummaryLine(
            check_name=result.check_name,
            status=status,
            metric=metric_val,
            threshold=threshold_val,
            severity=severity,
        )
        lines.append(str(line))

    lines.append("-" * 80)
    total = len(report.alert_events)
    failed = len(report.failed_checks)
    passed = total - failed
    lines.append(f"Total: {total}  Passed: {passed}  Failed: {failed}")
    overall = "PASSED" if report.passed else "FAILED"
    lines.append(f"Overall result: {overall}")
    return "\n".join(lines)


def print_summary(report: RunReport) -> None:
    """Print the formatted summary to stdout."""
    print(build_summary(report))
