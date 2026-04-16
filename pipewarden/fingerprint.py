"""Alert fingerprinting – stable identity keys for dedup and correlation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from pipewarden.runner import AlertEvent


@dataclass
class Fingerprint:
    pipeline: str
    check_name: str
    severity: str
    digest: str
    first_seen: datetime = field(default_factory=datetime.utcnow)
    occurrences: int = 1

    def __str__(self) -> str:  # noqa: D401
        return (
            f"Fingerprint({self.digest[:8]}) "
            f"{self.pipeline}/{self.check_name} "
            f"[{self.severity}] x{self.occurrences}"
        )


def compute_digest(event: AlertEvent) -> str:
    """Return a stable SHA-256 hex digest for *event*."""
    payload = json.dumps(
        {
            "pipeline": event.rule.pipeline,
            "check": event.result.check_name,
            "severity": event.rule.severity,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class FingerprintStore:
    _records: List[Fingerprint] = field(default_factory=list)

    def record(self, event: AlertEvent) -> Fingerprint:
        digest = compute_digest(event)
        for fp in self._records:
            if fp.digest == digest:
                fp.occurrences += 1
                return fp
        fp = Fingerprint(
            pipeline=event.rule.pipeline,
            check_name=event.result.check_name,
            severity=event.rule.severity,
            digest=digest,
        )
        self._records.append(fp)
        return fp

    def get(self, digest: str) -> Optional[Fingerprint]:
        return next((r for r in self._records if r.digest == digest), None)

    def all(self) -> List[Fingerprint]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()
