"""Tests for pipewarden.fingerprint."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewarden.fingerprint import (
    Fingerprint,
    FingerprintStore,
    compute_digest,
)


def _make_event(pipeline="pipe_a", check="row_count", severity="warning"):
    rule = MagicMock()
    rule.pipeline = pipeline
    rule.severity = severity
    result = MagicMock()
    result.check_name = check
    event = MagicMock()
    event.rule = rule
    event.result = result
    return event


class TestComputeDigest:
    def test_same_event_same_digest(self):
        e1 = _make_event()
        e2 = _make_event()
        assert compute_digest(e1) == compute_digest(e2)

    def test_different_pipeline_different_digest(self):
        e1 = _make_event(pipeline="a")
        e2 = _make_event(pipeline="b")
        assert compute_digest(e1) != compute_digest(e2)

    def test_digest_is_64_hex_chars(self):
        assert len(compute_digest(_make_event())) == 64


class TestFingerprintStore:
    def test_first_record_creates_entry(self):
        store = FingerprintStore()
        fp = store.record(_make_event())
        assert fp.occurrences == 1
        assert len(store.all()) == 1

    def test_duplicate_event_increments_occurrences(self):
        store = FingerprintStore()
        store.record(_make_event())
        fp = store.record(_make_event())
        assert fp.occurrences == 2
        assert len(store.all()) == 1

    def test_different_events_create_separate_entries(self):
        store = FingerprintStore()
        store.record(_make_event(pipeline="a"))
        store.record(_make_event(pipeline="b"))
        assert len(store.all()) == 2

    def test_get_returns_fingerprint_by_digest(self):
        store = FingerprintStore()
        event = _make_event()
        store.record(event)
        digest = compute_digest(event)
        fp = store.get(digest)
        assert fp is not None
        assert fp.digest == digest

    def test_get_unknown_digest_returns_none(self):
        store = FingerprintStore()
        assert store.get("deadbeef" * 8) is None

    def test_clear_empties_store(self):
        store = FingerprintStore()
        store.record(_make_event())
        store.clear()
        assert store.all() == []


class TestFingerprintStr:
    def test_str_contains_digest_prefix(self):
        store = FingerprintStore()
        fp = store.record(_make_event())
        assert fp.digest[:8] in str(fp)

    def test_str_contains_pipeline(self):
        store = FingerprintStore()
        fp = store.record(_make_event(pipeline="my_pipe"))
        assert "my_pipe" in str(fp)

    def test_str_contains_occurrences(self):
        store = FingerprintStore()
        store.record(_make_event())
        fp = store.record(_make_event())
        assert "x2" in str(fp)
