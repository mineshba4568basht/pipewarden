"""Pipeline health check implementations for pipewarden."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    ERROR = "error"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str
    value: Optional[Any] = None
    threshold: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == CheckStatus.PASS

    def __str__(self) -> str:
        return f"[{self.status.value.upper()}] {self.name}: {self.message}"


def check_row_count(
    actual: int,
    min_count: Optional[int] = None,
    max_count: Optional[int] = None,
    name: str = "row_count",
) -> CheckResult:
    """Check that a dataset's row count falls within expected bounds."""
    if min_count is not None and actual < min_count:
        return CheckResult(
            name=name,
            status=CheckStatus.FAIL,
            message=f"Row count {actual} is below minimum {min_count}",
            value=actual,
            threshold=min_count,
        )
    if max_count is not None and actual > max_count:
        return CheckResult(
            name=name,
            status=CheckStatus.FAIL,
            message=f"Row count {actual} exceeds maximum {max_count}",
            value=actual,
            threshold=max_count,
        )
    return CheckResult(
        name=name,
        status=CheckStatus.PASS,
        message=f"Row count {actual} is within expected range",
        value=actual,
    )


def check_null_rate(
    null_count: int,
    total_count: int,
    max_rate: float = 0.05,
    column: str = "unknown",
    name: str = "null_rate",
) -> CheckResult:
    """Check that the null rate for a column does not exceed the threshold."""
    if total_count == 0:
        return CheckResult(
            name=name,
            status=CheckStatus.ERROR,
            message="Cannot compute null rate: total_count is zero",
        )
    rate = null_count / total_count
    if rate > max_rate:
        return CheckResult(
            name=name,
            status=CheckStatus.FAIL,
            message=f"Null rate {rate:.2%} for '{column}' exceeds max {max_rate:.2%}",
            value=rate,
            threshold=max_rate,
            metadata={"column": column},
        )
    return CheckResult(
        name=name,
        status=CheckStatus.PASS,
        message=f"Null rate {rate:.2%} for '{column}' is acceptable",
        value=rate,
        threshold=max_rate,
        metadata={"column": column},
    )


def check_freshness(
    age_seconds: float,
    max_age_seconds: float,
    name: str = "freshness",
) -> CheckResult:
    """Check that data is not older than the allowed maximum age."""
    if age_seconds > max_age_seconds:
        return CheckResult(
            name=name,
            status=CheckStatus.FAIL,
            message=f"Data is {age_seconds:.0f}s old, exceeds max {max_age_seconds:.0f}s",
            value=age_seconds,
            threshold=max_age_seconds,
        )
    return CheckResult(
        name=name,
        status=CheckStatus.PASS,
        message=f"Data freshness OK ({age_seconds:.0f}s old)",
        value=age_seconds,
        threshold=max_age_seconds,
    )
