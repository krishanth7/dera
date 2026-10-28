"""Cross-engine compatibility tests for Phase 6.2 Structural Reconstruction."""

import unittest

from dera.metadata.enums import CanonicalTypeCategory
from dera.reverse_engineering.reconstruction.builder import StructuralReconstructionBuilder
from tests.reverse_engineering.phase_6_2.fixtures import (
    build_mysql_fixture,
    build_postgres_enterprise_fixture,
    build_sqlite_fixture,
)


class TestCrossEngineReconstruction(unittest.TestCase):
    """Test structural reconstruction fidelity across PostgreSQL, SQLite, MySQL, and MariaDB."""

    def test_reconstruct_postgresql_enterprise(self) -> None:
        db = build_postgres_enterprise_fixture()
        builder = StructuralReconstructionBuilder()
        result = builder.build_from_canonical(db)

        self.assertEqual(result.engine, "postgresql")
        self.assertEqual(len(result.tables), 2)
        self.assertTrue(result.is_valid)

        orders = result.get_table_by_name("public", "orders")
        assert orders is not None
        # Check generated column
        tot_col = orders.get_column_by_name("total")
        assert tot_col is not None
        self.assertTrue(tot_col.generated_column.is_generated)
        self.assertEqual(tot_col.generated_column.expression, "subtotal + tax")

        # Check composite foreign key
        self.assertEqual(len(orders.foreign_keys), 1)
        self.assertTrue(orders.foreign_keys[0].is_composite)
        self.assertEqual(orders.foreign_keys[0].source_column_names, ("tenant_id", "customer_id"))
        self.assertEqual(orders.foreign_keys[0].referenced_column_names, ("tenant_id", "id"))

    def test_reconstruct_sqlite_strict_without_rowid(self) -> None:
        db = build_sqlite_fixture()
        builder = StructuralReconstructionBuilder()
        result = builder.build_from_canonical(db)

        self.assertEqual(result.engine, "sqlite")
        self.assertEqual(len(result.tables), 1)
        tbl = result.tables[0]
        self.assertEqual(tbl.native_name, "inventory")
        self.assertTrue(tbl.native_attributes.get("without_rowid"))
        self.assertTrue(tbl.native_attributes.get("is_strict"))

    def test_reconstruct_mysql_auto_increment_and_enum(self) -> None:
        db = build_mysql_fixture()
        builder = StructuralReconstructionBuilder()
        result = builder.build_from_canonical(db)

        self.assertEqual(result.engine, "mysql")
        tbl = result.tables[0]
        id_col = tbl.get_column_by_name("id")
        assert id_col is not None
        self.assertTrue(id_col.identity.is_auto_increment)
        self.assertEqual(id_col.identity.strategy, "AUTO_INCREMENT")

        status_col = tbl.get_column_by_name("status")
        assert status_col is not None
        self.assertEqual(status_col.canonical_type, CanonicalTypeCategory.ENUM)
        self.assertEqual(tbl.native_attributes.get("engine"), "InnoDB")


if __name__ == "__main__":
    unittest.main()
