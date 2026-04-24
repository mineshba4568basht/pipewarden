"""Tests for pipewarden.jitter."""
from __future__ import annotations

import random

import pytest

from pipewarden.jitter import JitterPolicy, JitterResult, apply_jitter


# ---------------------------------------------------------------------------
# JitterPolicy construction
# ---------------------------------------------------------------------------

class TestJitterPolicyConstruction:
    def test_defaults(self):
        p = JitterPolicy()
        assert p.strategy == "full"
        assert p.min_delay == 0.0
        assert p.max_delay == 30.0
        assert p.seed is None

    def test_custom_strategy(self):
        p = JitterPolicy(strategy="equal")
        assert p.strategy == "equal"

    def test_invalid_strategy_raises(self):
        with pytest.raises(ValueError, match="Invalid strategy"):
            JitterPolicy(strategy="random_walk")  # type: ignore[arg-type]

    def test_negative_min_delay_raises(self):
        with pytest.raises(ValueError, match="min_delay"):
            JitterPolicy(min_delay=-1.0)

    def test_zero_max_delay_raises(self):
        with pytest.raises(ValueError, match="max_delay"):
            JitterPolicy(max_delay=0.0)

    def test_min_gte_max_raises(self):
        with pytest.raises(ValueError, match="min_delay must be less than max_delay"):
            JitterPolicy(min_delay=10.0, max_delay=5.0)

    def test_str_contains_strategy(self):
        p = JitterPolicy(strategy="decorrelated", min_delay=1.0, max_delay=20.0)
        s = str(p)
        assert "decorrelated" in s
        assert "1.0" in s
        assert "20.0" in s


# ---------------------------------------------------------------------------
# JitterResult
# ---------------------------------------------------------------------------

class TestJitterResult:
    def test_str_contains_delays(self):
        r = JitterResult(base_delay=5.0, jittered_delay=3.14, strategy="full")
        s = str(r)
        assert "5.000" in s
        assert "3.140" in s
        assert "full" in s


# ---------------------------------------------------------------------------
# apply_jitter — full strategy
# ---------------------------------------------------------------------------

class TestApplyJitterFull:
    def test_result_within_bounds(self):
        policy = JitterPolicy(strategy="full", min_delay=0.0, max_delay=10.0)
        rng = random.Random(42)
        for base in [1.0, 5.0, 10.0, 20.0]:
            result = apply_jitter(policy, base, _rng=rng)
            assert policy.min_delay <= result.jittered_delay <= policy.max_delay

    def test_strategy_stored(self):
        policy = JitterPolicy(strategy="full")
        result = apply_jitter(policy, 5.0, _rng=random.Random(0))
        assert result.strategy == "full"

    def test_base_delay_stored(self):
        policy = JitterPolicy()
        result = apply_jitter(policy, 7.5, _rng=random.Random(1))
        assert result.base_delay == 7.5


# ---------------------------------------------------------------------------
# apply_jitter — equal strategy
# ---------------------------------------------------------------------------

class TestApplyJitterEqual:
    def test_result_at_least_half_base(self):
        policy = JitterPolicy(strategy="equal", min_delay=0.0, max_delay=30.0)
        rng = random.Random(99)
        for _ in range(20):
            result = apply_jitter(policy, 10.0, _rng=rng)
            # equal jitter: base/2 <= jittered <= base
            assert result.jittered_delay >= 5.0 - 1e-9
            assert result.jittered_delay <= 30.0


# ---------------------------------------------------------------------------
# apply_jitter — decorrelated strategy
# ---------------------------------------------------------------------------

class TestApplyJitterDecorrelated:
    def test_result_within_policy_bounds(self):
        policy = JitterPolicy(strategy="decorrelated", min_delay=1.0, max_delay=60.0)
        rng = random.Random(7)
        for base in [2.0, 5.0, 15.0]:
            result = apply_jitter(policy, base, _rng=rng)
            assert policy.min_delay <= result.jittered_delay <= policy.max_delay


# ---------------------------------------------------------------------------
# Seeded reproducibility
# ---------------------------------------------------------------------------

def test_seeded_policy_is_reproducible():
    policy = JitterPolicy(strategy="full", seed=123)
    r1 = apply_jitter(policy, 10.0)
    r2 = apply_jitter(policy, 10.0)
    assert r1.jittered_delay == r2.jittered_delay
