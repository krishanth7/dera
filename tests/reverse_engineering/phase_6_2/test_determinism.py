"""Determinism and reproducibility tests for Phase 6.2 Structural Reconstruction."""

import unittest

from dera.reverse_engineering.reconstruction.builder import StructuralReconstructionBuilder
from tests.reverse_engineering.phase_6_2.fixtures import (
    build_postgres_enterprise_fixture,
    build_schema_representation_fixture,
)


class TestStructuralDeterminism(unittest.TestCase):
    """Test deterministic hashing, input-order invariance, and composite key stability."""

    def test_repeated_reconstruction_produces_identical_hash(self) -> None:
        canonical_db = build_postgres_enterprise_fixture()
        schema = build_schema_representation_fixture(canonical_db)
        builder = StructuralReconstructionBuilder()

        res1 = builder.build(schema)
        res2 = builder.build(schema)

        self.assertEqual(res1.schema_hash, res2.schema_hash)
        self.assertEqual(len(res1.schema_hash), 64)

    def test_input_table_order_invariance(self) -> None:
        canonical_db = build_postgres_enterprise_fixture()

        # Build schema 1
        schema1 = build_schema_representation_fixture(canonical_db)

        # Reverse tables in canonical database
        ns = canonical_db.namespaces[0]
        reversed_ns = ns.model_copy(update={"tables": tuple(reversed(ns.tables))})
        reversed_db = canonical_db.model_copy(update={"namespaces": (reversed_ns,)})
        schema2 = build_schema_representation_fixture(reversed_db)

        builder = StructuralReconstructionBuilder()
        res1 = builder.build(schema1)
        res2 = builder.build(schema2)

        # Hashing and table sequence must be completely identical
        self.assertEqual(res1.schema_hash, res2.schema_hash)
        self.assertEqual([t.native_name for t in res1.tables], [t.native_name for t in res2.tables])

    def test_composite_primary_key_order_preserved_deterministically(self) -> None:
        canonical_db = build_postgres_enterprise_fixture()
        builder = StructuralReconstructionBuilder()
        res = builder.build_from_canonical(canonical_db)

        cust = res.get_table_by_name("public", "customers")
        self.assertIsNotNone(cust)
        assert cust is not None
        assert cust.primary_key is not None
        self.assertEqual(cust.primary_key.column_names, ("tenant_id", "id"))

        orders = res.get_table_by_name("public", "orders")
        self.assertIsNotNone(orders)
        assert orders is not None
        assert orders.primary_key is not None
        self.assertEqual(orders.primary_key.column_names, ("tenant_id", "order_id"))


if __name__ == "__main__":
    unittest.main()
