"""Example workflow demonstrating circuit breaker usage."""
from __future__ import annotations
from pipewarden.circuit_breaker import CircuitBreaker, CircuitState


def _simulate_pipeline(cb: CircuitBreaker, succeed: bool) -> str:
    if not cb.allow_request():
        return f"[BLOCKED] Circuit is {cb.state.value} for '{cb.pipeline}'"
    if succeed:
        cb.record_success()
        return f"[OK] '{cb.pipeline}' check passed"
    else:
        cb.record_failure()
        return f"[FAIL] '{cb.pipeline}' check failed (failures={cb._failures})"


def main() -> None:
    cb = CircuitBreaker(pipeline="orders_pipeline", failure_threshold=3, recovery_timeout=5)
    print("--- Simulating failures ---")
    for i in range(4):
        msg = _simulate_pipeline(cb, succeed=False)
        print(msg)

    print(f"\nCircuit state: {cb.state.value}")

    print("\n--- Attempting while OPEN ---")
    msg = _simulate_pipeline(cb, succeed=True)
    print(msg)

    print("\n--- Resetting circuit ---")
    cb.record_success()
    print(f"State after reset: {cb.state.value}")

    print("\n--- Normal operation ---")
    for _ in range(2):
        msg = _simulate_pipeline(cb, succeed=True)
        print(msg)


if __name__ == "__main__":
    main()
