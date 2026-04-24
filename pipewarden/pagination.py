"""Pagination support for listing historical records in CLI commands."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, List, TypeVar

T = TypeVar("T")

_DEFAULT_PAGE_SIZE = 20
_MAX_PAGE_SIZE = 500


@dataclass
class PageRequest:
    """Parameters for a paginated query."""

    page: int = 1
    page_size: int = _DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError(f"page must be >= 1, got {self.page}")
        if not (1 <= self.page_size <= _MAX_PAGE_SIZE):
            raise ValueError(
                f"page_size must be between 1 and {_MAX_PAGE_SIZE}, got {self.page_size}"
            )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    def __str__(self) -> str:
        return f"PageRequest(page={self.page}, page_size={self.page_size})"


@dataclass
class Page(Generic[T]):
    """A single page of results."""

    items: List[T]
    page: int
    page_size: int
    total: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return max(1, (self.total + self.page_size - 1) // self.page_size)

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    def __str__(self) -> str:
        return (
            f"Page {self.page}/{self.total_pages} "
            f"({len(self.items)} items, {self.total} total)"
        )


def paginate(items: List[T], request: PageRequest) -> Page[T]:
    """Slice *items* according to *request* and return a :class:`Page`."""
    total = len(items)
    sliced = items[request.offset : request.offset + request.page_size]
    return Page(
        items=sliced,
        page=request.page,
        page_size=request.page_size,
        total=total,
    )
