"""Tests for pipewarden.caching_cli."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock

import pytest

from pipewarden.caching import CachePolicy, ResultCache
from pipewarden.caching_cli import build_caching_parser, handle_caching, _cmd_clear, _cmd_info
from pipewarden.checks import CheckResult, CheckStatus


@pytest.fixture()
def caching_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    build_caching_parser(sub)
    return parser


@pytest.fixture()
def cache() -> ResultCache:
    return ResultCache()


class TestBuildCachingParser:
    def test_cache_subcommand_registered(self, caching_parser):
        args = caching_parser.parse_args(["cache", "info"])
        assert args.command == "cache"

    def test_info_default_ttl(self, caching_parser):
        args = caching_parser.parse_args(["cache", "info"])
        assert args.ttl == 300

    def test_info_default_max_entries(self, caching_parser):
        args = caching_parser.parse_args(["cache", "info"])
        assert args.max_entries == 256

    def test_info_custom_ttl(self, caching_parser):
        args = caching_parser.parse_args(["cache", "info", "--ttl", "60"])
        assert args.ttl == 60

    def test_clear_default_pipeline_none(self, caching_parser):
        args = caching_parser.parse_args(["cache", "clear"])
        assert args.pipeline is None

    def test_clear_stores_pipeline(self, caching_parser):
        args = caching_parser.parse_args(["cache", "clear", "--pipeline", "my_pipe"])
        assert args.pipeline == "my_pipe"

    def test_clear_stores_check(self, caching_parser):
        args = caching_parser.parse_args(["cache", "clear", "--check", "row_count"])
        assert args.check == "row_count"


class TestHandleCaching:
    def test_no_subcommand_prints_message(self, capsys, cache):
        args = argparse.Namespace(cache_cmd=None)
        handle_caching(args, cache)
        out = capsys.readouterr().out
        assert "No cache sub-command" in out

    def test_info_prints_policy(self, capsys, cache):
        args = argparse.Namespace(cache_cmd="info", ttl=120, max_entries=64)
        handle_caching(args, cache)
        out = capsys.readouterr().out
        assert "120" in out
        assert "64" in out

    def test_info_prints_current_entries(self, capsys, cache):
        args = argparse.Namespace(cache_cmd="info", ttl=300, max_entries=256)
        handle_caching(args, cache)
        out = capsys.readouterr().out
        assert "Current entries" in out

    def test_clear_all_prints_count(self, capsys, cache):
        result = CheckResult(
            rule_name="p", check_name="c", status=CheckStatus.PASS, value=1, threshold=0
        )
        cache.put(result)
        args = argparse.Namespace(cache_cmd="clear", pipeline=None, check=None)
        handle_caching(args, cache)
        out = capsys.readouterr().out
        assert "1" in out

    def test_clear_specific_entry(self, capsys, cache):
        result = CheckResult(
            rule_name="p", check_name="c", status=CheckStatus.PASS, value=1, threshold=0
        )
        cache.put(result)
        args = argparse.Namespace(cache_cmd="clear", pipeline="p", check="c")
        handle_caching(args, cache)
        out = capsys.readouterr().out
        assert "p::c" in out
        assert cache.size == 0
