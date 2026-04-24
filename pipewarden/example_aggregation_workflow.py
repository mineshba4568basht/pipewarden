"""Example showing how to use the aggregation module end-to-end."""

from __future__ import annotations

from datetime import datetime, timedelta

from pipewarden.aggregation import AggregationPolicy, aggregate
from pipewarden.config import AlertRule
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.runner import AlertEvent


def _fake_event(pipeline: str, severity: str = "warning", offset: int = 0) -> AlertEvent:
    rule = AlertRule(name="row_count", check="row_count", threshold=100, severity=severity)
    result = CheckResult(rule=rule, status=CheckStatus.FAIL, value=0.0)
    event = AlertEvent(pipeline=pipeline, check_result=result, rule=rule)
    event.triggered_at = datetime.utcnow() - timedelta(seconds=offset)
    return event


def main() -> None:
    events = [
        _fake_event("sales", severity="warning", offset=5),
        _fake_event("sales", severity="critical", offset=10),
        _fake_event("inventory", severity="warning", offset=20),
        _fake_event("inventory", severity="warning", offset=30),
        _fake_event("orders", severity="critical", offset=90),  # outside 60 s window
    ]

    policy = AggregationPolicy(window_seconds=60, max_events=50, group_by="pipeline")
    buckets = aggregate(events, policy)

    print(f"Policy : {policy}")
    print(f"Buckets: {len(buckets)}")
    for bucket in sorted(buckets, key=lambda b: b.key):
        print(f"  {bucket}  severities={bucket.severities}")

    # Group by severity instead
    policy2 = AggregationPolicy(window_seconds=60, group_by="severity")
    buckets2 = aggregate(events, policy2)
    print("\nGrouped by severity:")
    for bucket in sorted(buckets2, key=lambda b: b.key):
        print(f"  {bucket}")


if __name__ == "__main__":
    main()
