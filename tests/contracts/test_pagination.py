"""Tests for DERA pagination contracts and page info calculation (Phase 4.2)."""

from __future__ import annotations

import unittest

from dera_api.contracts.base import DeraBaseModel
from dera_api.contracts.metadata import ResponseMetadata
from dera_api.contracts.pagination import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    PageInfo,
    PaginatedResponse,
    PaginationParams,
)
from pydantic import ValidationError


class DummyRecord(DeraBaseModel):
    id: int
    name: str


class TestPaginationContracts(unittest.TestCase):
    """Validate PaginationParams bounds, PageInfo computation, and PaginatedResponse serialization."""

    def test_pagination_params_defaults(self) -> None:
        """Verify default pagination parameters."""
        params = PaginationParams()
        self.assertEqual(params.page, 1)
        self.assertEqual(params.page_size, DEFAULT_PAGE_SIZE)
        self.assertIsNone(params.cursor)

    def test_pagination_params_valid_custom(self) -> None:
        """Verify valid custom pagination values."""
        params = PaginationParams(page=3, page_size=50, cursor="base64cursor==")
        self.assertEqual(params.page, 3)
        self.assertEqual(params.page_size, 50)
        self.assertEqual(params.cursor, "base64cursor==")

    def test_pagination_params_page_bounds(self) -> None:
        """Verify page must be >= 1."""
        with self.assertRaises(ValidationError):
            PaginationParams(page=0)

        with self.assertRaises(ValidationError):
            PaginationParams(page=-5)

    def test_pagination_params_page_size_bounds(self) -> None:
        """Verify page_size bounds (1 to MAX_PAGE_SIZE)."""
        with self.assertRaises(ValidationError):
            PaginationParams(page_size=0)

        with self.assertRaises(ValidationError):
            PaginationParams(page_size=MAX_PAGE_SIZE + 1)

    def test_page_info_create_empty_dataset(self) -> None:
        """Verify PageInfo calculation for 0 total items."""
        page_info = PageInfo.create(page=1, page_size=20, total_items=0)
        self.assertEqual(page_info.page, 1)
        self.assertEqual(page_info.page_size, 20)
        self.assertEqual(page_info.total_items, 0)
        self.assertEqual(page_info.total_pages, 0)
        self.assertFalse(page_info.has_previous)
        self.assertFalse(page_info.has_next)

    def test_page_info_boundary_calculations(self) -> None:
        """Verify page info calculation across pagination boundaries."""
        cases = [
            (1, 20, 20, 1, False, False),
            (1, 20, 21, 2, False, True),
            (2, 20, 21, 2, True, False),
            (2, 10, 45, 5, True, True),
            (5, 10, 45, 5, True, False),
        ]
        for page, page_size, total_items, expected_pages, has_prev, has_next in cases:
            with self.subTest(page=page, page_size=page_size, total_items=total_items):
                info = PageInfo.create(page=page, page_size=page_size, total_items=total_items)
                self.assertEqual(info.total_pages, expected_pages)
                self.assertIs(info.has_previous, has_prev)
                self.assertIs(info.has_next, has_next)

    def test_paginated_response_serialization(self) -> None:
        """Verify PaginatedResponse[T] envelope structure."""
        items = [DummyRecord(id=1, name="first"), DummyRecord(id=2, name="second")]
        page_info = PageInfo.create(page=1, page_size=10, total_items=2)
        meta = ResponseMetadata(request_id="req-paginated-1")

        response = PaginatedResponse[DummyRecord](
            items=items,
            pagination=page_info,
            meta=meta,
        )

        dump = response.model_dump()
        self.assertEqual(len(dump["items"]), 2)
        self.assertEqual(dump["items"][0]["name"], "first")
        self.assertEqual(dump["pagination"]["total_items"], 2)
        self.assertEqual(dump["pagination"]["total_pages"], 1)
        self.assertEqual(dump["meta"]["request_id"], "req-paginated-1")
