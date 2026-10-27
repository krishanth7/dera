"""Determinism tests for Phase 6.1 Canonical Schema Representation."""

from __future__ import annotations

import unittest

from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.serialization import (
    serialize_schema_representation,
)

from tests.reverse_engineering.phase_6_1.fixtures import (
    build_enterprise_fixture,
    build_unicode_and_case_sensitive_fixture,
)


class TestDeterminism(unittest.TestCase):
    """Test suite ensuring byte-level determinism and input-order invariance."""

    def test_identical_metadata_produces_identical_hash(self) -> None:
        """Verify identical inputs produce identical cryptographic hash."""
        db1 = build_enterprise_fixture()
        db2 = build_enterprise_fixture()

        schema1 = SchemaBuilder.from_canonical_database(db1)
        schema2 = SchemaBuilder.from_canonical_database(db2)

        hash1 = schema1.compute_hash()
        hash2 = schema2.compute_hash()

        self.assertEqual(hash1, hash2)
        self.assertEqual(schema1.to_json(), schema2.to_json())

    def test_shuffled_namespaces_input_invariance(self) -> None:
        """Verify that reversing namespace input order results in identical schema output and hash."""
        db_orig = build_enterprise_fixture()
        # Reverse namespace order in input
        shuffled_db = db_orig.model_copy(update={"namespaces": tuple(reversed(db_orig.namespaces))})

        schema_orig = SchemaBuilder.from_canonical_database(db_orig)
        schema_shuffled = SchemaBuilder.from_canonical_database(shuffled_db)

        # Namespaces in output representation must be ordered deterministically
        self.assertEqual(
            [ns.name for ns in schema_orig.namespaces],
            [ns.name for ns in schema_shuffled.namespaces],
        )

        # Hash must be identical
        self.assertEqual(schema_orig.compute_hash(), schema_shuffled.compute_hash())

    def test_shuffled_tables_input_invariance(self) -> None:
        """Verify that reversing table order within a namespace yields identical schema output."""
        db_orig = build_enterprise_fixture()
        pub_ns = db_orig.get_namespace("public")
        self.assertIsNotNone(pub_ns)

        # Reverse tables: 'users', 'organizations'
        reversed_tables_ns = pub_ns.model_copy(update={"tables": tuple(reversed(pub_ns.tables))})
        analytics_ns = db_orig.get_namespace("analytics")
        self.assertIsNotNone(analytics_ns)

        shuffled_db = db_orig.model_copy(update={"namespaces": (reversed_tables_ns, analytics_ns)})

        schema_orig = SchemaBuilder.from_canonical_database(db_orig)
        schema_shuffled = SchemaBuilder.from_canonical_database(shuffled_db)

        self.assertEqual(
            [t.name for t in schema_orig.all_tables()],
            [t.name for t in schema_shuffled.all_tables()],
        )
        self.assertEqual(schema_orig.compute_hash(), schema_shuffled.compute_hash())

    def test_unicode_case_sensitive_determinism(self) -> None:
        """Verify determinism across multiple runs with Unicode and case-sensitive names."""
        db1 = build_unicode_and_case_sensitive_fixture()
        db2 = build_unicode_and_case_sensitive_fixture()

        s1 = SchemaBuilder.from_canonical_database(db1)
        s2 = SchemaBuilder.from_canonical_database(db2)

        self.assertEqual(s1.compute_hash(), s2.compute_hash())
        json1 = serialize_schema_representation(s1)
        json2 = serialize_schema_representation(s2)
        self.assertEqual(json1, json2)


if __name__ == "__main__":
    unittest.main()
