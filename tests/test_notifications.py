"""Tests for pipewarden.notifications."""
from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.config import AlertRule
from pipewarden.notifications import (
    NotificationDispatcher,
    NotificationResult,
    _build_slack_payload,
    send_slack,
)
from pipewarden.runner import AlertEvent


@pytest.fixture()
def passing_event() -> AlertEvent:
    rule = AlertRule(name="row_check", check="check_row_count", threshold=10)
    result = CheckResult(
        check_name="check_row_count",
        status=CheckStatus.PASS,
        message="rows=50 >= threshold=10",
    )
    return AlertEvent(rule=rule, result=result)


@pytest.fixture()
def failing_event() -> AlertEvent:
    rule = AlertRule(name="row_check", check="check_row_count", threshold=10, severity="critical")
    result = CheckResult(
        check_name="check_row_count",
        status=CheckStatus.FAIL,
        message="rows=2 < threshold=10",
    )
    return AlertEvent(rule=rule, result=result)


class TestNotificationResult:
    def test_str_success(self):
        r = NotificationResult(channel="slack", success=True, message="ok")
        assert str(r) == "[OK] slack: ok"

    def test_str_failure(self):
        r = NotificationResult(channel="slack", success=False, message="timeout")
        assert str(r) == "[FAIL] slack: timeout"


class TestBuildSlackPayload:
    def test_contains_rule_name(self, failing_event):
        payload = _build_slack_payload(failing_event)
        assert "row_check" in payload["text"]

    def test_contains_severity(self, failing_event):
        payload = _build_slack_payload(failing_event)
        assert "critical" in payload["text"]

    def test_pass_icon(self, passing_event):
        payload = _build_slack_payload(passing_event)
        assert ":white_check_mark:" in payload["text"]

    def test_fail_icon(self, failing_event):
        payload = _build_slack_payload(failing_event)
        assert ":red_circle:" in payload["text"]


class TestSendSlack:
    def test_success(self, failing_event):
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = b"ok"

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = send_slack("https://hooks.slack.com/fake", failing_event)

        assert result.success is True
        assert result.channel == "slack"

    def test_failure_on_url_error(self, failing_event):
        import urllib.error

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
            result = send_slack("https://hooks.slack.com/fake", failing_event)

        assert result.success is False
        assert "refused" in result.message


class TestNotificationDispatcher:
    def test_no_channels_returns_empty(self, failing_event):
        dispatcher = NotificationDispatcher()
        results = dispatcher.dispatch(failing_event)
        assert results == []

    def test_slack_channel_called(self, failing_event):
        dispatcher = NotificationDispatcher(slack_webhook="https://hooks.slack.com/fake")
        ok = NotificationResult(channel="slack", success=True, message="sent")
        with patch("pipewarden.notifications.send_slack", return_value=ok) as mock_send:
            results = dispatcher.dispatch(failing_event)
            mock_send.assert_called_once()
        assert len(results) == 1
        assert results[0].success is True

    def test_all_results_accumulates(self, failing_event):
        dispatcher = NotificationDispatcher(slack_webhook="https://hooks.slack.com/fake")
        ok = NotificationResult(channel="slack", success=True, message="sent")
        with patch("pipewarden.notifications.send_slack", return_value=ok):
            dispatcher.dispatch(failing_event)
            dispatcher.dispatch(failing_event)
        assert len(dispatcher.all_results) == 2
