"""Example demonstrating quota enforcement across repeated alert events."""
from __future__ import annotations

from pipewarden.config import AlertRule
from pipewarden.quota import QuotaManager, QuotaPolicy
from pipewarden.runner import AlertEvent


def _fake_event(pipeline: str = "orders") -> AlertEvent:
    rule = AlertRule(name="row_count", check="row_count", threshold=1000)
    return AlertEvent(pipeline=pipeline, rule=rule, observed=500.0)


def main() -> None:
    policy = QuotaPolicy(max_alerts=3, window_minutes=60)
    mgr = QuotaManager(policy=policy)

    print(f"Policy: {policy}")
    print()

    event = _fake_event()
    for i in range(5):
        result = mgr.check(event)
        status = "✓ ALLOWED" if result.allowed else "✗ BLOCKED"
        print(f"  Alert #{i + 1}: {status} ({result.current_count}/{result.limit})")

    print()
    print("Resetting quota for 'orders'...")
    mgr.reset("orders")
    result = mgr.check(event)
    print(f"  After reset: {'✓ ALLOWED' if result.allowed else '✗ BLOCKED'}")


if __name__ == "__main__":
    main()
