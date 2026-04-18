"""Webhook notification support for pipewarden alerts."""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from pipewarden.runner import AlertEvent


@dataclass
class WebhookConfig:
    url: str
    secret: Optional[str] = None
    timeout: int = 10

    def __post_init__(self) -> None:
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid webhook URL: {self.url!r}")
        if self.timeout < 1:
            raise ValueError("timeout must be >= 1")


@dataclass
class WebhookResult:
    url: str
    status_code: Optional[int]
    success: bool
    error: Optional[str] = None
    sent_at: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        state = "OK" if self.success else f"FAIL({self.error})"
        return f"[WebhookResult] {self.url} -> {state}"


def _build_payload(event: AlertEvent) -> bytes:
    data = {
        "pipeline": event.rule.pipeline,
        "check": event.rule.check_name,
        "severity": event.rule.severity,
        "message": event.message,
        "triggered_at": event.triggered_at.isoformat(),
    }
    return json.dumps(data).encode()


def send_webhook(event: AlertEvent, config: WebhookConfig) -> WebhookResult:
    payload = _build_payload(event)
    headers = {"Content-Type": "application/json"}
    if config.secret:
        headers["X-Pipewarden-Secret"] = config.secret
    req = urllib.request.Request(config.url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=config.timeout) as resp:
            return WebhookResult(url=config.url, status_code=resp.status, success=True)
    except Exception as exc:  # noqa: BLE001
        return WebhookResult(url=config.url, status_code=None, success=False, error=str(exc))
