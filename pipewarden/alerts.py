"""Alert dispatching module for pipewarden."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import logging

from pipewarden.runner import AlertEvent

logger = logging.getLogger(__name__)


@dataclass
class AlertRecord:
    """Represents a dispatched alert with metadata."""
    event: AlertEvent
    channel: str
    dispatched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = True
    error_message: Optional[str] = None

    def __str__(self) -> str:
        status = "OK" if self.success else f"FAILED: {self.error_message}"
        return (
            f"[{self.dispatched_at.isoformat()}] "
            f"Alert '{self.event.rule_name}' via {self.channel}: {status}"
        )


class AlertDispatcher:
    """Dispatches alerts based on alert events from a run report."""

    def __init__(self, channels: Optional[list] = None):
        self.channels = channels or ["log"]
        self._records: list[AlertRecord] = []

    def dispatch(self, event: AlertEvent) -> list[AlertRecord]:
        """Dispatch an alert event to all configured channels."""
        records = []
        for channel in self.channels:
            record = self._send(event, channel)
            self._records.append(record)
            records.append(record)
        return records

    def dispatch_all(self, events: list[AlertEvent]) -> list[AlertRecord]:
        """Dispatch multiple alert events."""
        all_records = []
        for event in events:
            all_records.extend(self.dispatch(event))
        return all_records

    def _send(self, event: AlertEvent, channel: str) -> AlertRecord:
        """Send alert to a specific channel."""
        try:
            if channel == "log":
                self._send_log(event)
            else:
                raise ValueError(f"Unsupported alert channel: '{channel}'")
            return AlertRecord(event=event, channel=channel, success=True)
        except Exception as exc:
            logger.error("Failed to dispatch alert via %s: %s", channel, exc)
            return AlertRecord(event=event, channel=channel, success=False, error_message=str(exc))

    def _send_log(self, event: AlertEvent) -> None:
        """Log the alert event."""
        level = logging.CRITICAL if event.severity == "critical" else logging.WARNING
        logger.log(level, "ALERT [%s] %s — %s", event.severity.upper(), event.rule_name, event.message)

    @property
    def records(self) -> list[AlertRecord]:
        return list(self._records)

    @property
    def failed_dispatches(self) -> list[AlertRecord]:
        return [r for r in self._records if not r.success]
