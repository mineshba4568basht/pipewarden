"""Tests for pipewarden.caching."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewarden.caching import CacheEntry, CachePolicy, ResultCache
from pipewarden.checks import CheckResult, CheckStatus


def _make_result(pipeline: str = "pipe_a", check: str = "row_count") -> CheckResult:
    return CheckResult(
        rule_name=pipeline,
        check_name=check,
        status=CheckStatus.PASS,
        value=100,
        threshold=10,
    )


# ---------------------------------------------------------------------------
# CachePolicy
# ---------------------------------------------------------------------------

class TestCachePolicy:
    def test_defaults(self):
        p = CachePolicy()
        assert p.ttl_seconds == 300
        assert p.max_entries == 256

    def test_invalid_ttl_raises(self):
        with pytest.raises(ValueError, match="ttl_seconds"):
            CachePolicy(ttl_seconds=0)

    def test_invalid_max_entries_raises(self):
        with pytest.raises(ValueError, match="max_entries"):
            CachePolicy(max_entries=-1)


# ---------------------------------------------------------------------------
# CacheEntry
# ---------------------------------------------------------------------------

class TestCacheEntry:
    def test_not_expired_immediately(self):
        entry = CacheEntry(result=_make_result(), ttl_seconds=60)
        assert not entry.is_expired()

    def test_expired_after_ttl(self):
        past = datetime.utcnow() - timedelta(seconds=400)
        entry = CacheEntry(result=_make_result(), cached_at=past, ttl_seconds=300)
        assert entry.is_expired()

    def test_exactly_at_boundary_is_expired(self):
        now = datetime.utcnow()
        boundary = now - timedelta(seconds=300)
        entry = CacheEntry(result=_make_result(), cached_at=boundary, ttl_seconds=300)
        assert entry.is_expired(now=now)


# ---------------------------------------------------------------------------
# ResultCache
# ---------------------------------------------------------------------------

@pytest.fixture()
def cache() -> ResultCache:
    return ResultCache(CachePolicy(ttl_seconds=300, max_entries=4))


class TestResultCache:
    def test_put_and_get(self, cache: ResultCache):
        r = _make_result()
        cache.put(r)
        assert cache.get("pipe_a", "row_count") is r

    def test_get_missing_returns_none(self, cache: ResultCache):
        assert cache.get("missing", "check") is None

    def test_get_expired_returns_none(self, cache: ResultCache):
        r = _make_result()
        cache.put(r)
        # Manually expire the entry
        key = "pipe_a::row_count"
        cache._store[key].cached_at = datetime.utcnow() - timedelta(seconds=400)
        assert cache.get("pipe_a", "row_count") is None

    def test_size_reflects_entries(self, cache: ResultCache):
        cache.put(_make_result("a", "c1"))
        cache.put(_make_result("b", "c2"))
        assert cache.size == 2

    def test_invalidate_removes_entry(self, cache: ResultCache):
        cache.put(_make_result())
        removed = cache.invalidate("pipe_a", "row_count")
        assert removed is True
        assert cache.size == 0

    def test_invalidate_missing_returns_false(self, cache: ResultCache):
        assert cache.invalidate("nope", "nope") is False

    def test_clear_returns_count(self, cache: ResultCache):
        cache.put(_make_result("a", "c1"))
        cache.put(_make_result("b", "c2"))
        assert cache.clear() == 2
        assert cache.size == 0

    def test_evicts_oldest_when_at_capacity(self):
        small_cache = ResultCache(CachePolicy(ttl_seconds=300, max_entries=2))
        small_cache.put(_make_result("a", "c"))
        small_cache.put(_make_result("b", "c"))
        small_cache.put(_make_result("c", "c"))  # should evict "a::c"
        assert small_cache.size == 2
        assert small_cache.get("a", "c") is None
