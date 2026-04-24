"""Alert scoring — assign a numeric health score to a pipeline run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from pipewarden.runner import AlertEvent

_SEVERITY_WEIGHT: dict[str, int] = {
    "critical": 40,
    "warning": 15,
    "info": 5,
}
_MAX_SCORE = 100


@dataclass
class ScoringPolicy:
    """Weights used when computing a pipeline health score."""

    critical_weight: int = 40
    warning_weight: int = 15
    info_weight: int = 5
    max_score: int = 100

    def __post_init__(self) -> None:
        for attr in ("critical_weight", "warning_weight", "info_weight", "max_score"):
            if getattr(self, attr) < 0:
                raise ValueError(f"{attr} must be >= 0")
        if self.max_score == 0:
            raise ValueError("max_score must be > 0")

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"ScoringPolicy(critical={self.critical_weight}, "
            f"warning={self.warning_weight}, info={self.info_weight}, "
            f"max={self.max_score})"
        )


@dataclass
class ScoreResult:
    """Outcome of scoring a list of alert events."""

    pipeline: str
    score: int
    max_score: int
    event_count: int
    deductions: List[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        """True when the score is above 50 % of the maximum."""
        return self.score > self.max_score // 2

    @property
    def pct(self) -> float:
        if self.max_score == 0:
            return 0.0
        return round(self.score / self.max_score * 100, 1)

    def __str__(self) -> str:
        status = "HEALTHY" if self.healthy else "UNHEALTHY"
        return (
            f"[{status}] {self.pipeline}: score={self.score}/{self.max_score} "
            f"({self.pct}%) events={self.event_count}"
        )


def score_pipeline(
    pipeline: str,
    events: List[AlertEvent],
    policy: ScoringPolicy | None = None,
) -> ScoreResult:
    """Return a :class:`ScoreResult` for *pipeline* given *events*."""
    if policy is None:
        policy = ScoringPolicy()

    weight_map = {
        "critical": policy.critical_weight,
        "warning": policy.warning_weight,
        "info": policy.info_weight,
    }

    deductions: list[str] = []
    total_deducted = 0
    for ev in events:
        sev = ev.rule.severity.lower()
        w = weight_map.get(sev, 0)
        if w:
            deductions.append(f"{ev.rule.name}(-{w})")
            total_deducted += w

    raw = policy.max_score - total_deducted
    score = max(0, min(policy.max_score, raw))
    return ScoreResult(
        pipeline=pipeline,
        score=score,
        max_score=policy.max_score,
        event_count=len(events),
        deductions=deductions,
    )
