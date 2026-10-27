"""Golden File tests for Phase 6.1 Canonical Schema Representation."""

from __future__ import annotations

import json
import unittest

from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.schema import SCHEMA_REPRESENTATION_CONTRACT_VERSION
from dera.reverse_engineering.serialization import (
    compute_schema_hash,
    serialize_schema_representation,
)

from tests.reverse_engineering.phase_6_1.fixtures import build_enterprise_fixture


class TestGoldenSchema(unittest.TestCase):
    """Test suite ensuring byte-level canonical schema serialization matches reviewed golden output."""

    def test_golden_enterprise_schema(self) -> None:
        """Verify SchemaRepresentation exact structure, fields, and determinism against golden contract."""
        db = build_enterprise_fixture(
            engine="postgresql",
            workspace_id="ws_golden",
            db_name="golden_enterprise_db",
        )
        schema = SchemaBuilder.from_canonical_database(
            db, workspace_id="ws_golden", strict_validation=True
        )

        self.assertEqual(schema.contract_version, SCHEMA_REPRESENTATION_CONTRACT_VERSION)
        self.assertEqual(schema.database_name, "golden_enterprise_db")
        self.assertEqual(schema.engine, "postgresql")
        self.assertTrue(schema.is_validated)
        self.assertEqual(len(schema.validation_issues), 0)

        # Namespaces
        self.assertEqual(len(schema.namespaces), 2)
        ns_names = [ns.name for ns in schema.namespaces]
        self.assertEqual(ns_names, ["analytics", "public"])

        # Tables
        tables = schema.all_tables()
        self.assertEqual(len(tables), 2)
        self.assertEqual([t.name for t in tables], ["organizations", "users"])

        # Foreign Key References
        self.assertEqual(len(schema.foreign_key_references), 1)
        fk = schema.foreign_key_references[0]
        self.assertEqual(fk.foreign_key_name, "fk_users_org")
        self.assertEqual(fk.source_table_name, "users")
        self.assertEqual(fk.referenced_table_name, "organizations")
        self.assertTrue(fk.is_resolved)

        # Serialization
        serialized = serialize_schema_representation(schema, indent=2)
        parsed = json.loads(serialized)

        self.assertEqual(parsed["contract_version"], "1.0.0")
        self.assertEqual(parsed["database_name"], "golden_enterprise_db")
        self.assertEqual(parsed["engine"], "postgresql")
        self.assertIn("namespaces", parsed)
        self.assertIn("foreign_key_references", parsed)
        self.assertIn("resource_metrics", parsed)
        self.assertTrue(parsed["is_validated"])

        # Deterministic Hash Check
        h1 = schema.compute_hash()
        h2 = compute_schema_hash(schema)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)


if __name__ == "__main__":
    unittest.main()
