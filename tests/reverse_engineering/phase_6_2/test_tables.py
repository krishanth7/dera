"""Unit tests for table reconstruction in Phase 6.2."""

import unittest

from dera.reverse_engineering.reconstruction.tables import reconstruct_table
from tests.reverse_engineering.phase_6_2.fixtures import (
    build_postgres_enterprise_fixture,
    build_sqlite_fixture,
)


class TestTableReconstruction(unittest.TestCase):
    """Test full table reconstruction, column aggregation, and query helpers."""

    def test_reconstruct_postgres_table(self) -> None:
        canonical_db = build_postgres_enterprise_fixture()
        customers_table = canonical_db.namespaces[0].tables[0]

        reconstructed = reconstruct_table(customers_table, "postgresql")
        self.assertEqual(reconstructed.native_name, "customers")
        self.assertEqual(reconstructed.namespace, "public")
        self.assertEqual(len(reconstructed.columns), 4)

        # Primary key verification
        self.assertIsNotNone(reconstructed.primary_key)
        assert reconstructed.primary_key is not None
        self.assertTrue(reconstructed.has_composite_primary_key)
        self.assertEqual(reconstructed.primary_key.column_names, ("tenant_id", "id"))

        # Unique constraint verification
        self.assertEqual(len(reconstructed.unique_constraints), 1)
        self.assertEqual(reconstructed.unique_constraints[0].column_names, ("tenant_id", "email"))

        # Column helpers
        col_tenant = reconstructed.get_column_by_name("tenant_id")
        self.assertIsNotNone(col_tenant)
        assert col_tenant is not None
        self.assertEqual(col_tenant.native_type, "uuid")

        self.assertIsNone(reconstructed.get_column_by_name("non_existent"))

    def test_reconstruct_sqlite_table_native_attributes(self) -> None:
        canonical_db = build_sqlite_fixture()
        inv_table = canonical_db.namespaces[0].tables[0]

        reconstructed = reconstruct_table(inv_table, "sqlite")
        self.assertEqual(reconstructed.native_name, "inventory")
        self.assertTrue(reconstructed.native_attributes.get("without_rowid"))
        self.assertTrue(reconstructed.native_attributes.get("is_strict"))
        self.assertEqual(len(reconstructed.check_constraints), 1)
        self.assertEqual(reconstructed.check_constraints[0].expression, "quantity >= 0")


if __name__ == "__main__":
    unittest.main()
