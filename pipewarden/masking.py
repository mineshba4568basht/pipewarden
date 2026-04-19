"""Field masking for sensitive data in alert events."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import re

_DEFAULT_PATTERNS = [
    r"password",
    r"secret",
    r"token",
    r"api[_-]?key",
]

MASK = "***"


@dataclass
class MaskingPolicy:
    patterns: List[str] = field(default_factory=lambda: list(_DEFAULT_PATTERNS))
    mask: str = MASK

    def __post_init__(self) -> None:
        if not self.mask:
            raise ValueError("mask string must not be empty")
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.patterns]

    def is_sensitive(self, key: str) -> bool:
        return any(rx.search(key) for rx in self._compiled)

    def apply(self, data: dict) -> dict:
        """Return a copy of *data* with sensitive values replaced."""
        return {
            k: (self.mask if self.is_sensitive(k) else v)
            for k, v in data.items()
        }

    def __str__(self) -> str:
        return f"MaskingPolicy(patterns={self.patterns}, mask={self.mask!r})"


@dataclass
class MaskResult:
    original_keys: List[str]
    masked_keys: List[str]
    data: dict

    def __str__(self) -> str:
        return (
            f"MaskResult(masked={self.masked_keys}, "
            f"clean={[k for k in self.original_keys if k not in self.masked_keys]})"
        )


def mask_event_metadata(metadata: dict, policy: Optional[MaskingPolicy] = None) -> MaskResult:
    """Apply *policy* to *metadata* and return a MaskResult."""
    if policy is None:
        policy = MaskingPolicy()
    masked_keys = [k for k in metadata if policy.is_sensitive(k)]
    return MaskResult(
        original_keys=list(metadata.keys()),
        masked_keys=masked_keys,
        data=policy.apply(metadata),
    )
