"""DERA API — Pagination Contracts.

Provides typed, bounded pagination query parameters and standardized
response structures supporting offset and cursor-based pagination.
"""

import math
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field

from dera_api.contracts.metadata import ResponseMetadata

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


class PaginationParams(BaseModel):
    """Query parameter contract for paginated requests."""

    model_config = ConfigDict(frozen=True)

    page: int = Field(
        default=1,
        ge=1,
        description="1-based page index for offset pagination.",
    )
    page_size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Number of records requested per page (maximum {MAX_PAGE_SIZE}).",
    )
    cursor: str | None = Field(
        default=None,
        description="Opaque token for deterministic cursor-based traversal.",
    )


class PageInfo(BaseModel):
    """Metadata describing pagination state and navigation links."""

    model_config = ConfigDict(frozen=True)

    page: int = Field(..., ge=1, description="Current page index.")
    page_size: int = Field(..., ge=1, le=MAX_PAGE_SIZE, description="Items returned per page.")
    total_items: int | None = Field(default=None, ge=0, description="Total count across all pages.")
    total_pages: int | None = Field(
        default=None, ge=0, description="Total number of pages available."
    )
    has_next: bool = Field(
        default=False, description="Flag indicating if a subsequent page exists."
    )
    has_previous: bool = Field(default=False, description="Flag indicating if a prior page exists.")
    next_cursor: str | None = Field(
        default=None, description="Opaque cursor token for subsequent page."
    )

    @classmethod
    def create(
        cls,
        page: int,
        page_size: int,
        total_items: int | None = None,
        next_cursor: str | None = None,
    ) -> "PageInfo":
        """Calculates total pages and traversal indicators deterministically."""
        total_pages = None
        has_next = False
        has_previous = page > 1

        if total_items is not None:
            total_pages = math.ceil(total_items / page_size) if page_size > 0 else 0
            has_next = page < total_pages
        elif next_cursor is not None:
            has_next = True

        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            next_cursor=next_cursor,
        )


class PaginatedResponse[T](BaseModel):
    """Standardized response contract for paginated collections."""

    model_config = ConfigDict(frozen=True)

    items: list[T] = Field(..., description="Collection of items for the active page.")
    pagination: PageInfo = Field(..., description="Pagination navigation metadata.")
    meta: ResponseMetadata = Field(
        default_factory=ResponseMetadata,
        description="Response metadata and correlation tracking.",
    )
