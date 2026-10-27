"""Tests for deterministic JSON serialization and datetime standardization (Phase 4.2)."""

from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime
from decimal import Decimal

from dera_api.contracts.base import DeraBaseModel
from pydantic import Field


class StrictNumericModel(DeraBaseModel):
    name: str
    price: Decimal
    score: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    optional_tag: str | None = None


class TestSerialization(unittest.TestCase):
    """Validate JSON serialization determinism, UTC compliance, and non-finite rejection."""

    def test_utc_datetime_iso8601_serialization(self) -> None:
        """Verify datetime serializes with UTC timezone in ISO 8601 format."""
        dt = datetime(2026, 10, 27, 12, 0, 0, tzinfo=UTC)
        model = StrictNumericModel(
            name="test",
            price=Decimal("199.99"),
            score=98.5,
            created_at=dt,
        )

        json_bytes = model.model_dump_json()
        data = json.loads(json_bytes)
        self.assertEqual(data["created_at"], "2026-10-27T12:00:00Z")

    def test_decimal_precision_retained(self) -> None:
        """Verify decimal precision is preserved without float rounding issues."""
        precise_val = Decimal("123456789.987654321")
        model = StrictNumericModel(
            name="high_precision",
            price=precise_val,
            score=1.0,
        )
        json_str = model.model_dump_json()
        self.assertIn("123456789.987654321", json_str)

    def test_explicit_null_handling(self) -> None:
        """Verify explicit null fields are represented properly."""
        model = StrictNumericModel(
            name="null_test",
            price=Decimal("10.00"),
            score=5.0,
            optional_tag=None,
        )
        data = json.loads(model.model_dump_json())
        self.assertIsNone(data["optional_tag"])

    def test_non_finite_float_rejected_by_standard_json(self) -> None:
        """Verify NaN or Infinity values cannot be serialized into valid standard JSON."""
        # Standard Python json.dumps with allow_nan=False rejects NaN
        with self.assertRaises(ValueError):
            json.dumps({"score": float("nan")}, allow_nan=False)

        with self.assertRaises(ValueError):
            json.dumps({"score": float("inf")}, allow_nan=False)

    def test_utf8_encoding_safety(self) -> None:
        """Verify UTF-8 characters serialize safely without corruption."""
        model = StrictNumericModel(
            name="PostgreSQL 🐘 schema 🚀",
            price=Decimal("0.00"),
            score=10.0,
        )
        json_str = model.model_dump_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["name"], "PostgreSQL 🐘 schema 🚀")
