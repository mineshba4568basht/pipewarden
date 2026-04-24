"""Tests for pipewarden.pagination and pipewarden.pagination_cli."""
from __future__ import annotations

import argparse
import pytest

from pipewarden.pagination import Page, PageRequest, paginate
from pipewarden.pagination_cli import (
    add_pagination_args,
    build_pagination_parser,
    page_from_args,
)


# ---------------------------------------------------------------------------
# PageRequest
# ---------------------------------------------------------------------------

class TestPageRequest:
    def test_defaults(self):
        req = PageRequest()
        assert req.page == 1
        assert req.page_size == 20

    def test_offset_first_page(self):
        req = PageRequest(page=1, page_size=10)
        assert req.offset == 0

    def test_offset_second_page(self):
        req = PageRequest(page=2, page_size=10)
        assert req.offset == 10

    def test_invalid_page_raises(self):
        with pytest.raises(ValueError, match="page must be"):
            PageRequest(page=0)

    def test_invalid_page_size_zero_raises(self):
        with pytest.raises(ValueError, match="page_size"):
            PageRequest(page_size=0)

    def test_invalid_page_size_too_large_raises(self):
        with pytest.raises(ValueError, match="page_size"):
            PageRequest(page_size=501)

    def test_str_contains_page_and_size(self):
        req = PageRequest(page=3, page_size=5)
        assert "3" in str(req)
        assert "5" in str(req)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

class TestPage:
    def _make(self, total: int, page: int = 1, page_size: int = 10) -> Page:
        items = list(range(page_size))
        return Page(items=items, page=page, page_size=page_size, total=total)

    def test_total_pages_exact(self):
        page = self._make(total=30, page_size=10)
        assert page.total_pages == 3

    def test_total_pages_with_remainder(self):
        page = self._make(total=31, page_size=10)
        assert page.total_pages == 4

    def test_has_next_true(self):
        page = self._make(total=30, page=1, page_size=10)
        assert page.has_next is True

    def test_has_next_false_on_last_page(self):
        page = self._make(total=30, page=3, page_size=10)
        assert page.has_next is False

    def test_has_prev_false_on_first_page(self):
        page = self._make(total=30, page=1)
        assert page.has_prev is False

    def test_has_prev_true_on_second_page(self):
        page = self._make(total=30, page=2)
        assert page.has_prev is True

    def test_str_contains_page_info(self):
        page = self._make(total=30, page=2, page_size=10)
        s = str(page)
        assert "2" in s
        assert "30" in s


# ---------------------------------------------------------------------------
# paginate()
# ---------------------------------------------------------------------------

class TestPaginate:
    def test_first_page_returns_correct_slice(self):
        items = list(range(25))
        page = paginate(items, PageRequest(page=1, page_size=10))
        assert page.items == list(range(10))

    def test_second_page_returns_correct_slice(self):
        items = list(range(25))
        page = paginate(items, PageRequest(page=2, page_size=10))
        assert page.items == list(range(10, 20))

    def test_last_partial_page(self):
        items = list(range(25))
        page = paginate(items, PageRequest(page=3, page_size=10))
        assert page.items == list(range(20, 25))

    def test_total_preserved(self):
        items = list(range(7))
        page = paginate(items, PageRequest(page=1, page_size=3))
        assert page.total == 7


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def pagination_parser() -> argparse.ArgumentParser:
    return build_pagination_parser()


class TestBuildPaginationParser:
    def test_demo_subcommand_registered(self, pagination_parser):
        args = pagination_parser.parse_args(["demo"])
        assert args.cmd == "demo"

    def test_demo_default_total(self, pagination_parser):
        args = pagination_parser.parse_args(["demo"])
        assert args.total == 50

    def test_page_default_is_one(self, pagination_parser):
        args = pagination_parser.parse_args(["demo"])
        assert args.page == 1

    def test_page_size_default(self, pagination_parser):
        args = pagination_parser.parse_args(["demo"])
        assert args.page_size == 20

    def test_custom_page_and_size(self, pagination_parser):
        args = pagination_parser.parse_args(["demo", "--page", "3", "--page-size", "5"])
        assert args.page == 3
        assert args.page_size == 5


def test_page_from_args_builds_request():
    parser = argparse.ArgumentParser()
    add_pagination_args(parser)
    args = parser.parse_args(["--page", "2", "--page-size", "15"])
    req = page_from_args(args)
    assert req.page == 2
    assert req.page_size == 15
