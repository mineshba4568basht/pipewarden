"""Notification channel integrations for PipeWarden alerts."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional

from pipewarden.runner import AlertEvent


@dataclass
class NotificationResult:
    channel: str
    success: bool
    message: str = ""

    def __str__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"[{status}] {self.channel}: {self.message}"


def _build_slack_payload(event: AlertEvent) -> dict:
    icon = ":white_check_mark:" if event.passed else ":red_circle:"
    text = (
        f"{icon} *PipeWarden Alert* — rule `{event.rule.name}`\n"
        f"Check: `{event.result.check_name}` | "
        f"Severity: `{event.rule.severity}`\n"
        f"Status: `{event.result.status.}` — {event.result.message}"
    )
    return {"text": text}


def send_slack(webhook_url: str, event: AlertEvent) -> NotificationResult:
    """POST an alert event to a Slack incoming webhook."""
    payload = _build_slack_payload(event)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode()
            return NotificationResult(channel="slack", success=True, message=body or "sent")
    except urllib.error.URLError as exc:
        return NotificationResult(channel="slack", success=False, message=str(exc))


@dataclass
class NotificationDispatcher:
    """Dispatch alert events to configured notification channels."""

    slack_webhook: Optional[str] = None
    _results: list[NotificationResult] = field(default_factory=list, init=False, repr=False)

    def dispatch(self, event: AlertEvent) -> list[NotificationResult]:
        results: list[NotificationResult] = []
        if self.slack_webhook:
            result = send_slack(self.slack_webhook, event)
            results.append(result)
        self._results.extend(results)
        return results

    @property
    def all_results(self) -> list[NotificationResult]:
        return list(self._results)
