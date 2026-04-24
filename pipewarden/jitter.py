"""Jitter policy for randomising retry/alert delays to avoid thundering herd."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

JitterStrategy = Literal["full", "equal", "decorrelated"]

_VALID_STRATEGIES: frozenset[str] = frozenset({"full", "equal", "decorrelated"})


@dataclass
class JitterPolicy:
    """Configures how jitter is applied to a base delay."""

    strategy: JitterStrategy = "full"
    min_delay: float = 0.0  # seconds
    max_delay: float = 30.0  # seconds
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.strategy not in _VALID_STRATEGIES:
            raise ValueError(
                f"Invalid strategy {self.strategy!r}. "
                f"Must be one of {sorted(_VALID_STRATEGIES)}."
            )
        if self.min_delay < 0:
            raise ValueError("min_delay must be >= 0.")
        if self.max_delay <= 0:
            raise ValueError("max_delay must be > 0.")
        if self.min_delay >= self.max_delay:
            raise ValueError("min_delay must be less than max_delay.")

    def __str__(self) -> str:
        return (
            f"JitterPolicy(strategy={self.strategy}, "
            f"min={self.min_delay}s, max={self.max_delay}s)"
        )


@dataclass
class JitterResult:
    """Outcome of applying jitter to a base delay."""

    base_delay: float
    jittered_delay: float
    strategy: JitterStrategy

    def __str__(self) -> str:
        return (
            f"JitterResult(base={self.base_delay:.3f}s, "
            f"jittered={self.jittered_delay:.3f}s, strategy={self.strategy})"
        )


def apply_jitter(
    policy: JitterPolicy,
    base_delay: float,
    *,
    _rng: random.Random | None = None,
) -> JitterResult:
    """Return a *JitterResult* with a randomised delay derived from *base_delay*.

    Strategies
    ----------
    full        : delay = uniform(min_delay, base_delay)
    equal       : delay = base_delay/2 + uniform(0, base_delay/2)
    decorrelated: delay = uniform(min_delay, prev * 3)  (prev = base_delay here)
    """
    rng = _rng or (random.Random(policy.seed) if policy.seed is not None else random)

    lo = policy.min_delay
    hi = min(base_delay, policy.max_delay)

    if hi < lo:
        hi = lo

    if policy.strategy == "full":
        jittered = rng.uniform(lo, hi) if hi > lo else lo
    elif policy.strategy == "equal":
        half = hi / 2.0
        jittered = half + rng.uniform(0, half)
    else:  # decorrelated
        jittered = rng.uniform(lo, min(base_delay * 3, policy.max_delay))

    jittered = max(policy.min_delay, min(jittered, policy.max_delay))
    return JitterResult(base_delay=base_delay, jittered_delay=jittered, strategy=policy.strategy)
