"""CLI helpers that expose pagination controls for list sub-commands."""
from __future__ import annotations

import argparse
from typing import List

from pipewarden.pagination import Page, PageRequest, paginate

_DEFAULT_PAGE_SIZE = 20


def add_pagination_args(parser: argparse.ArgumentParser) -> None:
    """Attach ``--page`` and ``--page-size`` arguments to *parser*."""
    parser.add_argument(
        "--page",
        type=int,
        default=1,
        metavar="N",
        help="Page number to display (default: 1).",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=_DEFAULT_PAGE_SIZE,
        metavar="N",
        help=f"Number of items per page (default: {_DEFAULT_PAGE_SIZE}).",
    )


def page_from_args(args: argparse.Namespace) -> PageRequest:
    """Build a :class:`PageRequest` from parsed CLI *args*."""
    return PageRequest(page=args.page, page_size=args.page_size)


def print_page(page: Page) -> None:  # type: ignore[type-arg]
    """Print *page* items and a footer showing pagination state."""
    for item in page.items:
        print(item)
    print(
        f"\n-- {page} --"
        + ("  [use --page to navigate]" if page.total_pages > 1 else "")
    )


def build_pagination_parser() -> argparse.ArgumentParser:
    """Return a standalone demo parser for the pagination sub-command."""
    parser = argparse.ArgumentParser(
        prog="pipewarden pagination",
        description="Pagination utilities (demo).",
    )
    sub = parser.add_subparsers(dest="cmd")
    demo = sub.add_parser("demo", help="Show a paginated demo list.")
    demo.add_argument("--total", type=int, default=50, help="Total fake items.")
    add_pagination_args(demo)
    return parser


def handle_pagination(args: argparse.Namespace) -> None:
    """Dispatch pagination CLI commands."""
    if args.cmd == "demo":
        items = [f"item-{i:03d}" for i in range(1, args.total + 1)]
        req = page_from_args(args)
        page = paginate(items, req)
        print_page(page)
    else:
        build_pagination_parser().print_help()
