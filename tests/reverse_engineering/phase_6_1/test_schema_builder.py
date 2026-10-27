"""Unit and Contract tests for SchemaBuilder."""

from __future__ import annotations

import unittest

from dera.reverse_engineering.builder import SchemaBuilder, SchemaResourceLimits
from dera.reverse_engineering.errors import (
    InvalidSchemaInputError,
    SchemaResourceLimitError,
    UnsupportedSchemaContractError,
)
from dera.reverse_engineering.schema import (
    SCHEMA_REPRESENTATION_CONTRACT_VERSION,
    SchemaRepresentation,
)

from tests.reverse_engineering.phase_6_1.fixtures import (
    build_enterprise_fixture,
    build_sqlite_fixture,
)


class TestSchemaBuilder(unittest.TestCase):
    """Test suite for SchemaBuilder deterministic construction."""

    def setUp(self) -> None:
        self.enterprise_db = build_enterprise_fixture()

    def test_build_from_canonical_database(self) -> None:
        """Verify building SchemaRepresentation from CanonicalDatabase."""
        schema = SchemaBuilder.from_canonical_database(self.enterprise_db)
        self.assertIsInstance(schema, SchemaRepresentation)
        self.assertEqual(schema.contract_version, SCHEMA_REPRESENTATION_CONTRACT_VERSION)
        self.assertEqual(schema.database_id, self.enterprise_db.id)
        self.assertEqual(schema.database_name, "enterprise_db")
        self.assertEqual(schema.engine, "postgresql")
        self.assertEqual(len(schema.namespaces), 2)
        self.assertTrue(schema.is_validated)
        self.assertEqual(len(schema.validation_issues), 0)

        # Check total objects in registry
        self.assertGreater(schema.total_objects, 10)
        self.assertIn("total_objects", schema.resource_metrics)
        self.assertIsNotNone(schema.build_duration_ms)

    def test_build_from_metadata_dict(self) -> None:
        """Verify building from raw dictionary representation."""
        raw_dict = self.enterprise_db.model_dump(mode="json")
        schema = SchemaBuilder.from_metadata(raw_dict)
        self.assertEqual(schema.database_id, self.enterprise_db.id)
        self.assertEqual(schema.database_name, self.enterprise_db.name)

    def test_build_from_metadata_invalid_type(self) -> None:
        """Verify error when passing invalid input type."""
        with self.assertRaises(InvalidSchemaInputError):
            SchemaBuilder.from_metadata(["invalid", "list"])  # type: ignore

    def test_unsupported_contract_version(self) -> None:
        """Verify UnsupportedSchemaContractError when contract_version is invalid."""
        raw_dict = self.enterprise_db.model_dump(mode="json")
        raw_dict["contract_version"] = "99.0.0"
        with self.assertRaises(UnsupportedSchemaContractError):
            SchemaBuilder.from_metadata(raw_dict)

    def test_resource_limit_max_objects(self) -> None:
        """Verify SchemaResourceLimitError when max_total_objects is exceeded."""
        limits = SchemaResourceLimits(max_total_objects=3)
        with self.assertRaises(SchemaResourceLimitError) as ctx:
            SchemaBuilder.from_canonical_database(self.enterprise_db, limits=limits)
        self.assertEqual(ctx.exception.limit_name, "max_total_objects")
        self.assertEqual(ctx.exception.limit_value, 3)

    def test_resource_limit_max_identifier_length(self) -> None:
        """Verify SchemaResourceLimitError when identifier is excessively long."""
        limits = SchemaResourceLimits(max_identifier_length=5)
        # Table 'organizations' is 13 chars > 5 chars limit
        with self.assertRaises(SchemaResourceLimitError) as ctx:
            SchemaBuilder.from_canonical_database(self.enterprise_db, limits=limits)
        self.assertIn("max_identifier_length", ctx.exception.limit_name)

    def test_resource_limit_max_definition_bytes(self) -> None:
        """Verify SchemaResourceLimitError on excessively large SQL bodies."""
        limits = SchemaResourceLimits(max_definition_bytes=10)
        # View definition in enterprise_db is > 10 bytes
        with self.assertRaises(SchemaResourceLimitError) as ctx:
            SchemaBuilder.from_canonical_database(self.enterprise_db, limits=limits)
        self.assertIn("max_definition_bytes", ctx.exception.limit_name)

    def test_sqlite_fixture_build(self) -> None:
        """Verify building SQLite schema representation."""
        sqlite_db = build_sqlite_fixture()
        schema = SchemaBuilder.from_canonical_database(sqlite_db)
        self.assertEqual(schema.engine, "sqlite")
        self.assertEqual(len(schema.namespaces), 1)
        self.assertEqual(len(schema.all_tables()), 1)
        tbl = schema.all_tables()[0]
        self.assertEqual(tbl.name, "items")
        self.assertTrue(schema.is_validated)


if __name__ == "__main__":
    unittest.main()
