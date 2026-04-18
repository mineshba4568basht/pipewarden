"""Circuit breaker pattern for pipeline alert dispatching."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class CircuitState(str, Enum):
    CLOSED = "closed"      # normal operation
    OPEN = "open"          # blocking calls
    HALF_OPEN = "half_open"  # testing recovery


@dataclass
class CircuitBreaker:
    pipeline: str
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    _failures: int = field(default=0, repr=False)
    _state: CircuitState = field(default=CircuitState.CLOSED, repr=False)
    _opened_at: Optional[datetime] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.recovery_timeout < 1:
            raise ValueError("recovery_timeout must be >= 1")

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN and self._opened_at:
            elapsed = (datetime.utcnow() - self._opened_at).total_seconds()
            if elapsed >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = datetime.utcnow()

    def record_success(self) -> None:
        self._failures = 0
        self._state = CircuitState.CLOSED
        self._opened_at = None

    def allow_request(self) -> bool:
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def __str__(self) -> str:
        return (
            f"CircuitBreaker(pipeline={self.pipeline!r}, "
            f"state={self.state.value}, failures={self._failures})"
        )


@dataclass
class CircuitBreakerRegistry:
    _breakers: dict[str, CircuitBreaker] = field(default_factory=dict)

    def get(self, pipeline: str, **kwargs) -> CircuitBreaker:
        if pipeline not in self._breakers:
            self._breakers[pipeline] = CircuitBreaker(pipeline=pipeline, **kwargs)
        return self._breakers[pipeline]

    def all(self) -> list[CircuitBreaker]:
        return list(self._breakers.values())

    def reset(self, pipeline: str) -> bool:
        if pipeline in self._breakers:
            self._breakers[pipeline].record_success()
            return True
        return False
