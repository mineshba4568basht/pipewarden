"""Alert priority scoring based on severity, recurrence, and pipeline tags."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

SEVERITY_SCORES = {"critical": 100, "warning": 50, "info": 10}


@dataclass
class PriorityScore:
    pipeline: str
    check: str
    base_score: int
    recurrence_bonus: int
    tag_bonus: int

    @property
    def total(self) -> int:
        return self.base_score + self.recurrence_bonus + self.tag_bonus

    def __str__(self) -> str:  # noqa: D105
        return (
            f"PriorityScore({self.pipeline}/{self.check}) "
            f"total={self.total} "
            f"[base={self.base_score} recurrence={self.recurrence_bonus} tag={self.tag_bonus}]"
        )


@dataclass
class PriorityPolicy:
    high_priority_tags: List[str] = field(default_factory=list)
    tag_bonus: int = 20
    recurrence_weight: int = 5
    max_recurrence_bonus: int = 50

    def __post_init__(self) -> None:
        if self.tag_bonus < 0:
            raise ValueError("tag_bonus must be >= 0")
        if self.recurrence_weight < 0:
            raise ValueError("recurrence_weight must be >= 0")
        if self.max_recurrence_bonus < 0:
            raise ValueError("max_recurrence_bonus must be >= 0")

    def score(self, event: object, recurrence: int = 1) -> PriorityScore:
        """Compute a PriorityScore for *event*.

        *event* is expected to have ``.rule.severity``, ``.rule.name``,
        ``.pipeline``, and optionally ``.rule.tags`` attributes.
        """
        severity = getattr(getattr(event, "rule", None), "severity", "info")
        base = SEVERITY_SCORES.get(severity, 10)

        rec_bonus = min(self.recurrence_weight * max(recurrence - 1, 0), self.max_recurrence_bonus)

        event_tags = getattr(getattr(event, "rule", None), "tags", []) or []
        t_bonus = self.tag_bonus if any(t in self.high_priority_tags for t in event_tags) else 0

        pipeline = getattr(event, "pipeline", "unknown")
        check = getattr(getattr(event, "rule", None), "name", "unknown")
        return PriorityScore(
            pipeline=pipeline,
            check=check,
            base_score=base,
            recurrence_bonus=rec_bonus,
            tag_bonus=t_bonus,
        )
