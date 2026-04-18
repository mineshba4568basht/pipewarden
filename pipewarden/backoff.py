"""Exponential back-off policy for alert retries."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class BackoffPolicy:
    base_delay: float = 60.0        # seconds
    multiplier: float = 2.0
    max_delay: float = 3600.0       # seconds
    max_attempts: int = 5

    def __post_init__(self) -> None:
        if self.base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if self.multiplier < 1.0:
            raise ValueError("multiplier must be >= 1.0")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")

    def delay_for(self, attempt: int) -> float:
        """Return delay in seconds for the given attempt number (1-based)."""
        raw = self.base_delay * math.pow(self.multiplier, attempt - 1)
        return min(raw, self.max_delay)

    def next_retry_at(self, last_attempt: datetime, attempt: int) -> Optional[datetime]:
        """Return when the next retry should occur, or None if exhausted."""
        if attempt >= self.max_attempts:
            return None
        return last_attempt + timedelta(seconds=self.delay_for(attempt + 1))

    def __str__(self) -> str:
        return (
            f"BackoffPolicy(base={self.base_delay}s, "
            f"x{self.multiplier}, max={self.max_delay}s, "
            f"attempts={self.max_attempts})"
        )


@dataclass
class BackoffState:
    pipeline: str
    check: str
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    _policy: BackoffPolicy = field(default_factory=BackoffPolicy, repr=False)

    def record_attempt(self) -> None:
        self.attempts += 1
        self.last_attempt = datetime.utcnow()

    def is_due(self, now: Optional[datetime] = None) -> bool:
        if self.last_attempt is None:
            return True
        if self.attempts >= self._policy.max_attempts:
            return False
        next_at = self._policy.next_retry_at(self.last_attempt, self.attempts)
        if next_at is None:
            return False
        return (now or datetime.utcnow()) >= next_at

    def reset(self) -> None:
        self.attempts = 0
        self.last_attempt = None


class BackoffManager:
    def __init__(self, policy: Optional[BackoffPolicy] = None) -> None:
        self._policy = policy or BackoffPolicy()
        self._states: Dict[str, BackoffState] = {}

    def _key(self, pipeline: str, check: str) -> str:
        return f"{pipeline}::{check}"

    def state(self, pipeline: str, check: str) -> BackoffState:
        k = self._key(pipeline, check)
        if k not in self._states:
            self._states[k] = BackoffState(pipeline, check, _policy=self._policy)
        return self._states[k]

    def should_alert(self, pipeline: str, check: str) -> bool:
        return self.state(pipeline, check).is_due()

    def record(self, pipeline: str, check: str) -> None:
        self.state(pipeline, check).record_attempt()

    def reset(self, pipeline: str, check: str) -> None:
        self.state(pipeline, check).reset()
