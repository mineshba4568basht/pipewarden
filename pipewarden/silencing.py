"""Silencing rules: suppress alerts for known/expected failures."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from pipewarden.runner import AlertEvent


@dataclass
class SilenceRule:
    """A rule that suppresses matching alert events."""

    pipeline: str  # glob pattern, e.g. "etl_*" or "my_pipeline"
    check: str = "*"  # glob pattern over check name
    reason: str = ""
    expires_at: Optional[datetime] = None  # None means never expires

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """Return True if this rule is still active (not expired)."""
        if self.expires_at is None:
            return True
        now = now or datetime.now(timezone.utc)
        # Make naive datetimes comparable
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now < exp

    def matches(self, event: AlertEvent, now: Optional[datetime] = None) -> bool:
        """Return True if this rule silences the given event."""
        if not self.is_active(now):
            return False
        pipeline_match = fnmatch.fnmatch(event.rule.pipeline, self.pipeline)
        check_match = fnmatch.fnmatch(event.result.check_name, self.check)
        return pipeline_match and check_match

    def __str__(self) -> str:
        expiry = self.expires_at.isoformat() if self.expires_at else "never"
        return (
            f"SilenceRule(pipeline={self.pipeline!r}, check={self.check!r}, "
            f"expires={expiry}, reason={self.reason!r})"
        )


@dataclass
class SilenceManager:
    """Manages a collection of silence rules."""

    rules: List[SilenceRule] = field(default_factory=list)

    def add(self, rule: SilenceRule) -> None:
        self.rules.append(rule)

    def remove_expired(self, now: Optional[datetime] = None) -> int:
        """Remove all expired rules and return the count of rules removed."""
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.is_active(now)]
        return before - len(self.rules)

    def is_silenced(
        self, event: AlertEvent, now: Optional[datetime] = None
    ) -> bool:
        """Return True if any active rule matches the event."""
        return any(r.matches(event, now) for r in self.rules)

    def filter_events(
        self, events: List[AlertEvent], now: Optional[datetime] = None
    ) -> List[AlertEvent]:
        """Return only events that are NOT silenced."""
        return [e for e in events if not self.is_silenced(e, now)]

    def active_rules(self, now: Optional[datetime] = None) -> List[SilenceRule]:
        """Return only rules that are currently active."""
        return [r for r in self.rules if r.is_active(now)]
