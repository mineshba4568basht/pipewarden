"""Tests for pipewarden.archiving."""
from __future__ import annotations

import gzip
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from pipewarden.archiving import ArchivePolicy, ArchiveResult, archive_entries


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _ts(hours_ago: float) -> str:
    return (NOW - timedelta(hours=hours_ago)).isoformat()


# ---------------------------------------------------------------------------
# ArchivePolicy
# ---------------------------------------------------------------------------

class TestArchivePolicy:
    def test_defaults(self):
        p = ArchivePolicy()
        assert p.max_age_hours == 168
        assert p.archive_path == ".pipewarden_archive.jsonl.gz"

    def test_invalid_max_age_raises(self):
        with pytest.raises(ValueError, match="max_age_hours"):
            ArchivePolicy(max_age_hours=0)

    def test_str_contains_max_age(self):
        p = ArchivePolicy(max_age_hours=48)
        assert "48" in str(p)


# ---------------------------------------------------------------------------
# ArchiveResult
# ---------------------------------------------------------------------------

class TestArchiveResult:
    def test_total(self):
        r = ArchiveResult(archived=3, remaining=7, archive_path="x.gz")
        assert r.total == 10

    def test_str_contains_archived(self):
        r = ArchiveResult(archived=5, remaining=2, archive_path="x.gz")
        assert "archived=5" in str(r)
        assert "remaining=2" in str(r)


# ---------------------------------------------------------------------------
# archive_entries
# ---------------------------------------------------------------------------

class TestArchiveEntries:
    def test_no_entries(self, tmp_path):
        policy = ArchivePolicy(archive_path=str(tmp_path / "arch.gz"))
        result = archive_entries([], policy, now=NOW)
        assert result.archived == 0
        assert result.remaining == 0

    def test_recent_entries_not_archived(self, tmp_path):
        entries = [{"timestamp": _ts(1), "pipeline": "p"}]
        policy = ArchivePolicy(max_age_hours=24, archive_path=str(tmp_path / "arch.gz"))
        result = archive_entries(entries, policy, now=NOW)
        assert result.archived == 0
        assert result.remaining == 1

    def test_old_entries_archived(self, tmp_path):
        arch = tmp_path / "arch.gz"
        entries = [{"timestamp": _ts(200), "pipeline": "p"}]
        policy = ArchivePolicy(max_age_hours=24, archive_path=str(arch))
        result = archive_entries(entries, policy, now=NOW)
        assert result.archived == 1
        assert result.remaining == 0
        assert arch.exists()

    def test_archive_file_contains_correct_data(self, tmp_path):
        arch = tmp_path / "arch.gz"
        old = {"timestamp": _ts(500), "pipeline": "old_pipe"}
        new = {"timestamp": _ts(2), "pipeline": "new_pipe"}
        policy = ArchivePolicy(max_age_hours=24, archive_path=str(arch))
        archive_entries([old, new], policy, now=NOW)
        with gzip.open(arch, "rb") as fh:
            lines = [json.loads(l) for l in fh if l.strip()]
        assert len(lines) == 1
        assert lines[0]["pipeline"] == "old_pipe"

    def test_mixed_entries(self, tmp_path):
        arch = tmp_path / "arch.gz"
        entries = [
            {"timestamp": _ts(300), "pipeline": "a"},
            {"timestamp": _ts(10), "pipeline": "b"},
            {"timestamp": _ts(400), "pipeline": "c"},
        ]
        policy = ArchivePolicy(max_age_hours=48, archive_path=str(arch))
        result = archive_entries(entries, policy, now=NOW)
        assert result.archived == 2
        assert result.remaining == 1

    def test_invalid_timestamp_treated_as_old(self, tmp_path):
        arch = tmp_path / "arch.gz"
        entries = [{"timestamp": "not-a-date", "pipeline": "p"}]
        policy = ArchivePolicy(max_age_hours=24, archive_path=str(arch))
        result = archive_entries(entries, policy, now=NOW)
        assert result.archived == 1
