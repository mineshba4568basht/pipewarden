"""Tests for the alert dispatching module."""
import logging
import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from pipewarden.alerts import AlertDispatcher, AlertRecord
from pipewarden.runner import AlertEvent


@pytest.fixture
def sample_event():
    return AlertEvent(
        rule_name="row_count_check",
        severity="warning",
        message="Row count 5 is below minimum threshold 10",
        check_name="orders_row_count",
    )


@pytest.fixture
def critical_event():
    return AlertEvent(
        rule_name="null_check",
        severity="critical",
        message="Null values detected in required column",
        check_name="orders_null_check",
    )


class TestAlertRecord:
    def test_str_success(self, sample_event):
        record = AlertRecord(event=sample_event, channel="log", success=True)
        assert "row_count_check" in str(record)
        assert "log" in str(record)
        assert "OK" in str(record)

    def test_str_failure(self, sample_event):
        record = AlertRecord(
            event=sample_event, channel="log", success=False, error_message="timeout"
        )
        assert "FAILED" in str(record)
        assert "timeout" in str(record)

    def test_dispatched_at_defaults_to_utc_now(self, sample_event):
        record = AlertRecord(event=sample_event, channel="log")
        assert record.dispatched_at.tzinfo == timezone.utc


class TestAlertDispatcher:
    def test_dispatch_log_channel_success(self, sample_event):
        dispatcher = AlertDispatcher(channels=["log"])
        records = dispatcher.dispatch(sample_event)
        assert len(records) == 1
        assert records[0].success is True
        assert records[0].channel == "log"

    def test_dispatch_logs_warning(self, sample_event, caplog):
        dispatcher = AlertDispatcher(channels=["log"])
        with caplog.at_level(logging.WARNING, logger="pipewarden.alerts"):
            dispatcher.dispatch(sample_event)
        assert "row_count_check" in caplog.text

    def test_dispatch_logs_critical(self, critical_event, caplog):
        dispatcher = AlertDispatcher(channels=["log"])
        with caplog.at_level(logging.CRITICAL, logger="pipewarden.alerts"):
            dispatcher.dispatch(critical_event)
        assert "CRITICAL" in caplog.text

    def test_dispatch_unsupported_channel(self, sample_event):
        dispatcher = AlertDispatcher(channels=["webhook"])
        records = dispatcher.dispatch(sample_event)
        assert len(records) == 1
        assert records[0].success is False
        assert "Unsupported" in records[0].error_message

    def test_dispatch_all_multiple_events(self, sample_event, critical_event):
        dispatcher = AlertDispatcher(channels=["log"])
        records = dispatcher.dispatch_all([sample_event, critical_event])
        assert len(records) == 2

    def test_records_accumulate(self, sample_event):
        dispatcher = AlertDispatcher(channels=["log"])
        dispatcher.dispatch(sample_event)
        dispatcher.dispatch(sample_event)
        assert len(dispatcher.records) == 2

    def test_failed_dispatches_filter(self, sample_event):
        dispatcher = AlertDispatcher(channels=["log", "webhook"])
        dispatcher.dispatch(sample_event)
        failed = dispatcher.failed_dispatches
        assert all(not r.success for r in failed)
        assert len(failed) == 1

    def test_default_channel_is_log(self, sample_event):
        dispatcher = AlertDispatcher()
        assert dispatcher.channels == ["log"]
