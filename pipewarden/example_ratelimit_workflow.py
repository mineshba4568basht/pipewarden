"""Example demonstrating rate limiting in a dispatch loop."""
from __future__ import annotations
from datetime import datetime, timedelta

from pipewarden.config import AlertRule
from pipewarden.runner import AlertEvent
from pipewarden.ratelimit import RateLimitPolicy, RateLimiter


def _fake_event(pipeline: str) -> AlertEvent:
    rule = AlertRule(name="row_count", check="row_count", threshold=100)
    return AlertEvent(pipeline=pipeline, rule=rule, value=10.0, message="Too few rows")


def main() -> None:
    policy = RateLimitPolicy(max_alerts=3, window_seconds=60)
    limiter = RateLimiter(policy)
    print(f"Policy: {policy}")

    now = datetime.utcnow()
    pipelines = ["sales", "sales", "sales", "sales", "inventory"]
    offsets = [0, 5, 10, 15, 2]

    for pipeline, offset in zip(pipelines, offsets):
        event = _fake_event(pipeline)
        ts = now + timedelta(seconds=offset)
        result = limiter.check(event, now=ts)
        print(result)

    print("\nResetting 'sales' counters...")
    limiter.reset("sales")
    result = limiter.check(_fake_event("sales"), now=now + timedelta(seconds=20))
    print(result)


if __name__ == "__main__":
    main()
