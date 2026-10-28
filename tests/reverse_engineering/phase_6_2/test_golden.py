"""Golden file tests for Phase 6.2 Structural Reconstruction."""

import unittest

from dera.reverse_engineering.reconstruction.builder import StructuralReconstructionBuilder
from tests.reverse_engineering.phase_6_2.fixtures import build_postgres_enterprise_fixture


class TestStructuralGolden(unittest.TestCase):
    """Test against a reviewed structural reconstruction snapshot."""

    def test_enterprise_golden_snapshot(self) -> None:
        db = build_postgres_enterprise_fixture(workspace_id="golden-ws")
        builder = StructuralReconstructionBuilder()
        result = builder.build_from_canonical(db)

        # Golden assertions
        self.assertEqual(result.contract_version, "1.0.0")
        self.assertEqual(result.database_name, "enterprise_db")
        self.assertEqual(result.engine, "postgresql")
        self.assertEqual(len(result.tables), 2)
        self.assertEqual(result.error_count, 0)
        self.assertEqual(result.warning_count, 0)

        # Hash is non-empty 64-char hex
        self.assertEqual(len(result.schema_hash), 64)

        # Verify tables structure
        table_names = [t.native_name for t in result.tables]
        self.assertEqual(table_names, ["customers", "orders"])

        orders = result.get_table_by_name("public", "orders")
        assert orders is not None
        self.assertEqual(len(orders.columns), 6)
        self.assertEqual(len(orders.foreign_keys), 1)
        self.assertEqual(len(orders.check_constraints), 1)


if __name__ == "__main__":
    unittest.main()
