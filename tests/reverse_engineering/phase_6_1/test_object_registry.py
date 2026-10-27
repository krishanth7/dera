"""Unit tests for ObjectRegistry."""

from __future__ import annotations

import unittest

from dera.metadata.enums import ObjectKind
from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.errors import (
    DuplicateRegistrationError,
    InvalidSchemaReferenceError,
)

from tests.reverse_engineering.phase_6_1.fixtures import build_enterprise_fixture


class TestObjectRegistry(unittest.TestCase):
    """Test suite for ObjectRegistry operations."""

    def setUp(self) -> None:
        self.enterprise_db = build_enterprise_fixture(workspace_id="ws_reg_test")
        self.schema = SchemaBuilder.from_canonical_database(
            self.enterprise_db, workspace_id="ws_reg_test"
        )
        self.registry = self.schema.registry

    def test_registry_workspace_scope_preserved(self) -> None:
        """Verify workspace_id is preserved on registry."""
        self.assertEqual(self.registry.workspace_id, "ws_reg_test")

    def test_duplicate_registration_raises_error(self) -> None:
        """Verify duplicate ObjectId registration strictly raises DuplicateRegistrationError."""
        # Attempt to register database ID again
        with self.assertRaises(DuplicateRegistrationError) as ctx:
            self.registry.register(self.enterprise_db.id, self.enterprise_db, ObjectKind.DATABASE)
        self.assertEqual(ctx.exception.object_id, self.enterprise_db.id)
        self.assertEqual(ctx.exception.object_kind, ObjectKind.DATABASE)

    def test_typed_retrieval_success(self) -> None:
        """Verify type-safe retrieval by ObjectId for each object kind."""
        # Database
        db = self.registry.get_database(self.enterprise_db.id)
        self.assertEqual(db.name, "enterprise_db")

        # Table
        tbl = self.schema.find_table("public", "organizations")
        self.assertIsNotNone(tbl)
        retrieved_tbl = self.registry.get_table(tbl.id)
        self.assertEqual(retrieved_tbl.name, "organizations")

        # Column
        col = tbl.columns[0]
        retrieved_col = self.registry.get_column(col.id)
        self.assertEqual(retrieved_col.name, col.name)

        # Primary Key Constraint
        self.assertIsNotNone(tbl.primary_key)
        retrieved_pk = self.registry.get_constraint(tbl.primary_key.id)
        self.assertEqual(retrieved_pk.name, tbl.primary_key.name)

    def test_typed_retrieval_wrong_kind_raises_error(self) -> None:
        """Verify InvalidSchemaReferenceError when looking up object with wrong kind method."""
        tbl = self.schema.find_table("public", "organizations")
        self.assertIsNotNone(tbl)
        # Attempting to get a table using get_column must fail
        with self.assertRaises(InvalidSchemaReferenceError) as ctx:
            self.registry.get_column(tbl.id)
        self.assertEqual(ctx.exception.reference_id, tbl.id)
        self.assertEqual(ctx.exception.expected_kind, ObjectKind.COLUMN)

    def test_typed_retrieval_missing_raises_error(self) -> None:
        """Verify InvalidSchemaReferenceError when object does not exist."""
        non_existent_id = "dera:table:000000000000000000000000"
        with self.assertRaises(InvalidSchemaReferenceError):
            self.registry.get_table(non_existent_id)

    def test_kind_indexed_queries(self) -> None:
        """Verify kind-indexed collection queries."""
        tables = self.registry.all_tables()
        self.assertEqual(len(tables), 2)
        table_names = {t.name for t in tables}
        self.assertEqual(table_names, {"organizations", "users"})

        namespaces = self.registry.all_namespaces()
        self.assertEqual(len(namespaces), 2)

        fks = self.registry.all_foreign_keys()
        self.assertEqual(len(fks), 1)
        self.assertEqual(fks[0].name, "fk_users_org")

    def test_contains_and_counts(self) -> None:
        """Verify contains check and statistics."""
        self.assertTrue(self.registry.contains(self.enterprise_db.id))
        self.assertFalse(self.registry.contains("dera:table:nonexistent"))
        self.assertGreater(len(self.registry), 10)
        counts = self.registry.object_count_by_kind()
        self.assertEqual(counts.get(ObjectKind.DATABASE), 1)
        self.assertEqual(counts.get(ObjectKind.NAMESPACE), 2)
        self.assertEqual(counts.get(ObjectKind.TABLE), 2)


if __name__ == "__main__":
    unittest.main()
