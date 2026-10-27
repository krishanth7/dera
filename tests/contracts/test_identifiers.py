"""Tests for DERA path and resource identifier validators (Phase 4.2)."""

from __future__ import annotations

import unittest

from dera_api.contracts.identifiers import (
    validate_db_identifier,
    validate_qualified_identifier,
    validate_slug,
    validate_uuid_str,
)


class TestIdentifiers(unittest.TestCase):
    """Validate identifier parsing, regex bounds, and injection prevention."""

    def test_validate_slug_valid(self) -> None:
        """Verify valid URL slugs."""
        self.assertEqual(validate_slug("public-schema"), "public-schema")
        self.assertEqual(validate_slug("warehouse-prod-01"), "warehouse-prod-01")
        self.assertEqual(validate_slug("catalog"), "catalog")

    def test_validate_slug_invalid(self) -> None:
        """Verify invalid URL slugs raise ValueError."""
        invalid_slugs = [
            "Uppercase-Slug",
            "has_underscore",
            "-leading-hyphen",
            "trailing-hyphen-",
            "slug with space",
            "../traversal",
            "",
            "x" * 65,  # Exceeds max length
        ]
        for candidate in invalid_slugs:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    validate_slug(candidate)

    def test_validate_uuid_str_valid(self) -> None:
        """Verify valid UUIDs are accepted and normalized to lowercase."""
        uuid_str = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        self.assertEqual(validate_uuid_str(uuid_str), uuid_str)
        self.assertEqual(validate_uuid_str(uuid_str.upper()), uuid_str)

    def test_validate_uuid_str_invalid(self) -> None:
        """Verify malformed UUIDs raise ValueError."""
        invalid_uuids = [
            "not-a-uuid",
            "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a1",  # Too short
            "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11-extra",
            "00000000-0000-0000-0000-00000000000g",  # Invalid hex char 'g'
            "",
        ]
        for candidate in invalid_uuids:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    validate_uuid_str(candidate)

    def test_validate_db_identifier_valid(self) -> None:
        """Verify standard database object identifiers."""
        self.assertEqual(validate_db_identifier("users"), "users")
        self.assertEqual(validate_db_identifier("order_items_2026"), "order_items_2026")
        self.assertEqual(validate_db_identifier("_internal_flag"), "_internal_flag")

    def test_validate_db_identifier_invalid(self) -> None:
        """Verify invalid SQL identifiers raise ValueError."""
        invalid_idents = [
            "123_starts_with_digit",
            "table-name-with-dash",
            "schema; DROP TABLE x",
            "user$info",
            "",
            "a" * 64,  # Exceeds standard PostgreSQL 63-byte limit
        ]
        for candidate in invalid_idents:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    validate_db_identifier(candidate)

    def test_validate_qualified_identifier(self) -> None:
        """Verify schema.table parsing."""
        schema, table = validate_qualified_identifier("public.users")
        self.assertEqual(schema, "public")
        self.assertEqual(table, "users")

        schema2, table2 = validate_qualified_identifier("accounts")
        self.assertIsNone(schema2)
        self.assertEqual(table2, "accounts")

    def test_validate_qualified_identifier_invalid(self) -> None:
        """Verify multi-part or invalid qualified identifiers fail."""
        with self.assertRaises(ValueError):
            validate_qualified_identifier("db.schema.table")  # 3 parts

        with self.assertRaises(ValueError):
            validate_qualified_identifier("public.invalid-table-name")
