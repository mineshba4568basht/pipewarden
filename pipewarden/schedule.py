"""Schedule management for pipewarden: parse cron-like schedule strings
and determine whether a pipeline run is due."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


_CRON_ALIASES: dict[str, str] = {
    "@hourly": "0 * * * *",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@weekly": "0 0 * * 0",
    "@monthly": "0 0 1 * *",
}


@dataclass
class CronSchedule:
    """Represents a simple 5-field cron expression (minute hour dom month dow)."""

    expression: str
    _fields: list[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        expr = _CRON_ALIASES.get(self.expression, self.expression)
        parts = expr.split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron expression '{self.expression}': expected 5 fields, got {len(parts)}"
            )
        self._fields = parts

    def _field_matches(self, value: int, field_str: str) -> bool:
        """Return True if *value* satisfies *field_str* (supports *, n, */n, n-m)."""
        if field_str == "*":
            return True
        if re.fullmatch(r"\*/\d+", field_str):
            step = int(field_str[2:])
            return value % step == 0
        if re.fullmatch(r"\d+-\d+", field_str):
            lo, hi = map(int, field_str.split("-"))
            return lo <= value <= hi
        if re.fullmatch(r"\d+", field_str):
            return value == int(field_str)
        raise ValueError(f"Unsupported cron field syntax: '{field_str}'")

    def is_due(self, at: Optional[datetime] = None) -> bool:
        """Return True if the schedule fires at the given datetime (default: now UTC)."""
        dt = at or datetime.now(tz=timezone.utc)
        minute, hour, dom, month, dow = self._fields
        return (
            self._field_matches(dt.minute, minute)
            and self._field_matches(dt.hour, hour)
            and self._field_matches(dt.day, dom)
            and self._field_matches(dt.month, month)
            and self._field_matches(dt.weekday(), dow)  # 0=Monday in Python
        )

    def __str__(self) -> str:
        return f"CronSchedule({self.expression!r})"


def parse_schedule(expression: str) -> CronSchedule:
    """Parse a cron expression string and return a :class:`CronSchedule`."""
    return CronSchedule(expression=expression)
