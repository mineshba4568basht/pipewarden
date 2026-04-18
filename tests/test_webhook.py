"""Tests for pipewarden.webhook."""
from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from pipewarden.config import AlertRule
from pipewarden.runner import AlertEvent
from pipewarden.webhook import WebhookConfig, WebhookResult, _build_payload, send_webhook


def _make_event(pipeline="pipe", check="row_count", severity="warning") -> AlertEvent:
    rule = AlertRule(pipeline=pipeline, check_name=check, severity=severity)
    return AlertEvent(rule=rule, message="test alert", triggered_at=datetime(2024, 1, 1, 12, 0))


class TestWebhookConfig:
    def test_valid_https_url(self):
        cfg = WebhookConfig(url="https://example.com/hook")
        assert cfg.url == "https://example.com/hook"

    def test_valid_http_url(self):
        cfg = WebhookConfig(url="http://localhost:8080/hook")
        assert cfg.timeout == 10

    def test_invalid_url_raises(self):
        with pytest.raises(ValueError, match="Invalid webhook URL"):
            WebhookConfig(url="ftp://bad")

    def test_invalid_timeout_raises(self):
        with pytest.raises(ValueError, match="timeout"):
            WebhookConfig(url="https://x.com", timeout=0)


class TestWebhookResult:
    def test_str_success(self):
        r = WebhookResult(url="https://x.com", status_code=200, success=True)
        assert "OK" in str(r)
        assert "https://x.com" in str(r)

    def test_str_failure(self):
        r = WebhookResult(url="https://x.com", status_code=None, success=False, error="timeout")
        assert "FAIL" in str(r)
        assert "timeout" in str(r)


class TestBuildPayload:
    def test_payload_contains_pipeline(self):
        event = _make_event(pipeline="my-pipe")
        raw = _build_payload(event)
        data = json.loads(raw)
        assert data["pipeline"] == "my-pipe"

    def test_payload_contains_severity(self):
        event = _make_event(severity="critical")
        data = json.loads(_build_payload(event))
        assert data["severity"] == "critical"

    def test_payload_is_bytes(self):
        event = _make_event()
        assert isinstance(_build_payload(event), bytes)


class TestSendWebhook:
    def test_successful_send(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            cfg = WebhookConfig(url="https://example.com/hook")
            result = send_webhook(_make_event(), cfg)
        assert result.success is True
        assert result.status_code == 200

    def test_failed_send_returns_error(self):
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            cfg = WebhookConfig(url="https://example.com/hook")
            result = send_webhook(_make_event(), cfg)
        assert result.success is False
        assert "connection refused" in result.error

    def test_secret_header_included(self):
        captured = {}

        def fake_urlopen(req, timeout):
            captured["headers"] = dict(req.headers)
            mock_resp = MagicMock()
            mock_resp.status = 204
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            cfg = WebhookConfig(url="https://example.com/hook", secret="s3cr3t")
            send_webhook(_make_event(), cfg)
        assert captured["headers"].get("X-pipewarden-secret") == "s3cr3t"
