"""Tests for pipewarden.enrichment."""
from __future__ import annotations

import pytest
from unittest.mock import patch

from pipewarden.config import AlertRule
from pipewarden.runner import AlertEvent
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.enrichment import (
    EnrichedEvent,
    EventEnricher,
    _enrich_environment,
    _enrich_hostname,
    _enrich_severity,
)


def _make_rule(name="test_rule", severity="warning") -> AlertRule:
    return AlertRule(name=name, metric="row_count", threshold=10, severity=severity)


def _make_event(rule: AlertRule | None = None) -> AlertEvent:
    r = rule or _make_rule()
    result = CheckResult(rule=r, status=CheckStatus.FAIL, value=5.0)
    return AlertEvent(rule=r, result=result)


@pytest.fixture
def event() -> AlertEvent:
    return _make_event()


class TestEnrichedEvent:
    def test_str_contains_rule_name(self, event):
        ee = EnrichedEvent(event=event, metadata={"k": "v"})
        assert "test_rule" in str(ee)

    def test_str_contains_metadata(self, event):
        ee = EnrichedEvent(event=event, metadata={"env": "staging"})
        assert "env=staging" in str(ee)

    def test_empty_metadata(self, event):
        ee = EnrichedEvent(event=event)
        assert "meta=[]" in str(ee)


class TestBuiltinEnrichers:
    def test_enrich_severity(self, event):
        meta = {}
        _enrich_severity(event, meta)
        assert meta["severity"] == "warning"

    def test_enrich_environment_default(self, event):
        meta = {}
        with patch.dict("os.environ", {}, clear=True):
            _enrich_environment(event, meta)
        assert meta["env"] == "production"

    def test_enrich_environment_custom(self, event):
        meta = {}
        with patch.dict("os.environ", {"PIPEWARDEN_ENV": "staging"}):
            _enrich_environment(event, meta)
        assert meta["env"] == "staging"

    def test_enrich_hostname(self, event):
        meta = {}
        _enrich_hostname(event, meta)
        assert "host" in meta
        assert isinstance(meta["host"], str)


class TestEventEnricher:
    def test_enrich_returns_enriched_event(self, event):
        enricher = EventEnricher()
        result = enricher.enrich(event)
        assert isinstance(result, EnrichedEvent)
        assert result.event is event

    def test_default_enrichers_populate_keys(self, event):
        enricher = EventEnricher()
        result = enricher.enrich(event)
        assert "severity" in result.metadata
        assert "host" in result.metadata
        assert "env" in result.metadata

    def test_custom_enricher_added(self, event):
        enricher = EventEnricher(enrichers=[])
        enricher.add(lambda e, m: m.update({"custom": "yes"}))
        result = enricher.enrich(event)
        assert result.metadata["custom"] == "yes"

    def test_enrich_all(self, event):
        enricher = EventEnricher()
        results = enricher.enrich_all([event, event])
        assert len(results) == 2
        assert all(isinstance(r, EnrichedEvent) for r in results)

    def test_no_enrichers_empty_metadata(self, event):
        enricher = EventEnricher(enrichers=[])
        result = enricher.enrich(event)
        assert result.metadata == {}
