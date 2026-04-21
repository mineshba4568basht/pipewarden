"""Redaction support for sensitive alert event fields."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pipewarden.runner import AlertEvent

_DEFAULT_PATTERNS: list[str] = [
    r"password",
    r"secret",
    r"token",
    r"api[_\-]?key",
    r"auth",
    r"credential",
]

_REDACTED = "***REDACTED***"


@dataclass
class RedactionPolicy:
    """Defines which metadata keys should be redacted."""

    patterns: list[str] = field(default_factory=lambda: list(_DEFAULT_PATTERNS))

    def __post_init__(self) -> None:
        if not self.patterns:
            raise ValueError("patterns must not be empty")
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.patterns]

    def is_sensitive(self, key: str) -> bool:
        """Return True if *key* matches any redaction pattern."""
        return any(rx.search(key) for rx in self._compiled)

    def apply(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Return a copy of *metadata* with sensitive values replaced."""
        return {
            k: (_REDACTED if self.is_sensitive(k) else v)
            for k, v in metadata.items()
        }

    def redact_event(self, event: AlertEvent) -> AlertEvent:
        """Return a new AlertEvent with sensitive metadata redacted."""
        clean_meta = self.apply(event.metadata)
        return AlertEvent(
            rule=event.rule,
            result=event.result,
            metadata=clean_meta,
        )

    def __str__(self) -> str:  # pragma: no cover
        return f"RedactionPolicy(patterns={self.patterns})"
