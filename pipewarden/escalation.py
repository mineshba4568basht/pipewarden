"""Escalation policy: re-alert when a check remains failing for N consecutive runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewarden.history import HistoryStore
from pipewarden.runner import AlertEvent


@dataclass
class EscalationPolicy:
    """Defines when a persistent failure should trigger an escalation alert."""

    pipeline: str
    check_name: str
    threshold: int = 3  # consecutive failures before escalating
    notify_every: int = 1  # re-escalate every N failures after threshold

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise ValueError("threshold must be >= 1")
        if self.notify_every < 1:
            raise ValueError("notify_every must be >= 1")

    def __str__(self) -> str:
        return (
            f"EscalationPolicy(pipeline={self.pipeline!r}, "
            f"check={self.check_name!r}, "
            f"threshold={self.threshold}, "
            f"notify_every={self.notify_every})"
        )


@dataclass
class EscalationResult:
    policy: EscalationPolicy
    consecutive_failures: int
    should_escalate: bool
    reason: str = ""

    def __str__(self) -> str:
        status = "ESCALATE" if self.should_escalate else "ok"
        return (
            f"[{status}] {self.policy.pipeline}/{self.policy.check_name} "
            f"— {self.consecutive_failures} consecutive failures "
            f"(threshold={self.policy.threshold})"
        )


def _count_consecutive_failures(store: HistoryStore, pipeline: str, check_name: str) -> int:
    """Return the number of most-recent consecutive failures for a check."""
    entries = store.load(pipeline)
    count = 0
    for entry in reversed(entries):
        failed = [e for e in (entry.events or []) if e.check_name == check_name]
        if not failed:
            break
        count += 1
    return count


def evaluate_escalation(
    policy: EscalationPolicy,
    store: HistoryStore,
) -> EscalationResult:
    """Evaluate whether the policy's escalation threshold has been crossed."""
    consecutive = _count_consecutive_failures(store, policy.pipeline, policy.check_name)

    if consecutive < policy.threshold:
        return EscalationResult(
            policy=policy,
            consecutive_failures=consecutive,
            should_escalate=False,
            reason=f"only {consecutive}/{policy.threshold} consecutive failures",
        )

    excess = consecutive - policy.threshold
    if excess % policy.notify_every == 0:
        return EscalationResult(
            policy=policy,
            consecutive_failures=consecutive,
            should_escalate=True,
            reason=f"threshold {policy.threshold} reached; notify_every={policy.notify_every}",
        )

    return EscalationResult(
        policy=policy,
        consecutive_failures=consecutive,
        should_escalate=False,
        reason=f"threshold crossed but not at notify_every boundary (excess={excess})",
    )


def batch_evaluate(
    policies: List[EscalationPolicy],
    store: HistoryStore,
) -> List[EscalationResult]:
    """Evaluate a list of escalation policies against the history store."""
    return [evaluate_escalation(p, store) for p in policies]
