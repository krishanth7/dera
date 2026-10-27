"""Tests for DERA API request schemas and validation behaviors (Phase 4.2)."""

from __future__ import annotations

import unittest

from dera_api.contracts.base import DeraBaseModel
from pydantic import Field, ValidationError


class SampleStrictRequest(DeraBaseModel):
    """Sample request model with strict fields and bounds."""

    name: str = Field(..., min_length=2, max_length=50, description="Resource name.")
    count: int = Field(..., ge=1, le=100, description="Item count between 1 and 100.")
    tags: list[str] = Field(default_factory=list, max_length=10, description="Optional tag list.")
    description: str | None = Field(
        default=None, max_length=200, description="Optional description."
    )


class TestRequestSchemas(unittest.TestCase):
    """Validate request model contracts, bounds, and rejection semantics."""

    def test_valid_request_deserialization(self) -> None:
        """Verify valid payload successfully instantiates request model."""
        payload = {
            "name": "production_cluster",
            "count": 42,
            "tags": ["prod", "postgres"],
            "description": "Primary database cluster",
        }
        model = SampleStrictRequest.model_validate(payload)
        self.assertEqual(model.name, "production_cluster")
        self.assertEqual(model.count, 42)
        self.assertEqual(model.tags, ["prod", "postgres"])
        self.assertEqual(model.description, "Primary database cluster")

    def test_missing_required_field_raises_validation_error(self) -> None:
        """Verify missing required fields trigger validation failure."""
        payload = {"count": 10}
        with self.assertRaises(ValidationError) as ctx:
            SampleStrictRequest.model_validate(payload)

        errors = ctx.exception.errors()
        missing_fields = [e["loc"][0] for e in errors if e["type"] == "missing"]
        self.assertIn("name", missing_fields)

    def test_string_length_bounds_enforced(self) -> None:
        """Verify minimum and maximum string constraints."""
        # Too short
        with self.assertRaises(ValidationError) as ctx:
            SampleStrictRequest.model_validate({"name": "a", "count": 5})
        self.assertTrue(any(e["loc"][0] == "name" for e in ctx.exception.errors()))

        # Too long
        with self.assertRaises(ValidationError) as ctx:
            SampleStrictRequest.model_validate({"name": "x" * 51, "count": 5})
        self.assertTrue(any(e["loc"][0] == "name" for e in ctx.exception.errors()))

    def test_numeric_bounds_enforced(self) -> None:
        """Verify integer ge and le constraints."""
        with self.assertRaises(ValidationError):
            SampleStrictRequest.model_validate({"name": "valid_name", "count": 0})

        with self.assertRaises(ValidationError):
            SampleStrictRequest.model_validate({"name": "valid_name", "count": 101})

    def test_collection_size_limits_enforced(self) -> None:
        """Verify max_length on collection fields."""
        oversized_tags = [f"tag_{i}" for i in range(11)]
        with self.assertRaises(ValidationError):
            SampleStrictRequest.model_validate(
                {
                    "name": "valid_name",
                    "count": 5,
                    "tags": oversized_tags,
                }
            )

    def test_nested_validation_contract(self) -> None:
        """Verify nested schema validation works deterministically."""

        class NestedParent(DeraBaseModel):
            title: str = Field(..., min_length=1)
            child: SampleStrictRequest

        valid_nested = {
            "title": "Config Group",
            "child": {
                "name": "child_node",
                "count": 10,
            },
        }
        parent = NestedParent.model_validate(valid_nested)
        self.assertEqual(parent.child.name, "child_node")

        invalid_nested = {
            "title": "Config Group",
            "child": {
                "name": "x",  # Too short
                "count": 10,
            },
        }
        with self.assertRaises(ValidationError) as ctx:
            NestedParent.model_validate(invalid_nested)

        errors = ctx.exception.errors()
        self.assertTrue(any("child" in e["loc"] and "name" in e["loc"] for e in errors))
