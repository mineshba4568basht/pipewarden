"""Tag-based filtering and grouping for pipeline checks."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from pipewarden.runner import RunReport, AlertEvent


@dataclass
class TagFilter:
    """Selects alert events whose rule tags overlap with *include_tags*.

    If *include_tags* is empty every event is accepted (no filtering).
    If *exclude_tags* is provided, events that match ANY excluded tag are
    dropped even when they match an include tag.
    """

    include_tags: frozenset[str] = field(default_factory=frozenset)
    exclude_tags: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        # Normalise to frozenset so the object is hashable
        if not isinstance(self.include_tags, frozenset):
            self.include_tags = frozenset(self.include_tags)
        if not isinstance(self.exclude_tags, frozenset):
            self.exclude_tags = frozenset(self.exclude_tags)

    def matches(self, event: AlertEvent) -> bool:
        """Return True when *event* passes the filter."""
        rule_tags: frozenset[str] = frozenset(getattr(event.rule, "tags", []) or [])
        if self.exclude_tags and rule_tags & self.exclude_tags:
            return False
        if not self.include_tags:
            return True
        return bool(rule_tags & self.include_tags)

    def apply(self, events: Iterable[AlertEvent]) -> list[AlertEvent]:
        """Return the subset of *events* that pass the filter."""
        return [e for e in events if self.matches(e)]


def group_by_tag(events: Iterable[AlertEvent]) -> dict[str, list[AlertEvent]]:
    """Partition *events* into buckets keyed by individual tag.

    An event with multiple tags appears in each relevant bucket.  Events
    with no tags are placed under the special key ``"(untagged)"``.
    """
    buckets: dict[str, list[AlertEvent]] = {}
    for event in events:
        rule_tags: Sequence[str] = getattr(event.rule, "tags", []) or []
        if not rule_tags:
            buckets.setdefault("(untagged)", []).append(event)
        else:
            for tag in rule_tags:
                buckets.setdefault(tag, []).append(event)
    return buckets


def filter_report_by_tags(
    report: RunReport,
    include_tags: Iterable[str] = (),
    exclude_tags: Iterable[str] = (),
) -> list[AlertEvent]:
    """Convenience wrapper: filter a report's alert events by tags."""
    tag_filter = TagFilter(
        include_tags=frozenset(include_tags),
        exclude_tags=frozenset(exclude_tags),
    )
    return tag_filter.apply(report.alert_events)
