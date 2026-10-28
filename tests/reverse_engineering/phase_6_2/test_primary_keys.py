"""Unit tests for primary key reconstruction in Phase 6.2."""

import unittest

from dera.metadata.enums import ConstraintType
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.models import CanonicalConstraint
from dera.reverse_engineering.reconstruction.columns import reconstruct_columns
from dera.reverse_engineering.reconstruction.errors import (
    ConstraintOwnershipError,
    PrimaryKeyReconstructionError,
)
from dera.reverse_engineering.reconstruction.primary_keys import reconstruct_primary_key

from tests.reverse_engineering.phase_6_2.fixtures import (
    make_test_column,
    make_test_provenance,
)


class TestPrimaryKeyReconstruction(unittest.TestCase):
    """Test single and composite primary key reconstruction and ownership checks."""

    def setUp(self) -> None:
        self.prov = make_test_provenance("postgresql")
        self.table_id = compute_stable_object_id("table", "postgresql", ("public", "orders"))
        c1 = make_test_column(str(self.table_id), "tenant_id", 1, "uuid")
        c2 = make_test_column(str(self.table_id), "order_id", 2, "bigint")
        c3 = make_test_column(str(self.table_id), "amount", 3, "numeric")
        self.columns = reconstruct_columns((c1, c2, c3), self.table_id, "postgresql")

    def test_single_column_primary_key(self) -> None:
        pk_id = compute_stable_object_id(
            "primary_key", "postgresql", (str(self.table_id), "pk_orders")
        )
        canonical_pk = CanonicalConstraint(
            id=pk_id,
            table_id=self.table_id,
            name="pk_orders",
            constraint_type=ConstraintType.PRIMARY_KEY,
            columns=("order_id",),
            provenance=self.prov,
        )
        pk = reconstruct_primary_key(canonical_pk, self.table_id, self.columns)
        self.assertIsNotNone(pk)
        assert pk is not None
        self.assertFalse(pk.is_composite)
        self.assertEqual(pk.column_names, ("order_id",))
        self.assertEqual(len(pk.column_ids), 1)

    def test_composite_primary_key_order_preserved(self) -> None:
        pk_id = compute_stable_object_id(
            "primary_key", "postgresql", (str(self.table_id), "pk_orders_composite")
        )
        # Specifically declared in order (tenant_id, order_id)
        canonical_pk = CanonicalConstraint(
            id=pk_id,
            table_id=self.table_id,
            name="pk_orders_composite",
            constraint_type=ConstraintType.PRIMARY_KEY,
            columns=("tenant_id", "order_id"),
            provenance=self.prov,
        )
        pk = reconstruct_primary_key(canonical_pk, self.table_id, self.columns)
        self.assertIsNotNone(pk)
        assert pk is not None
        self.assertTrue(pk.is_composite)
        self.assertEqual(pk.column_names, ("tenant_id", "order_id"))

    def test_column_not_in_table_raises_ownership_error(self) -> None:
        pk_id = compute_stable_object_id(
            "primary_key", "postgresql", (str(self.table_id), "pk_bad")
        )
        canonical_pk = CanonicalConstraint(
            id=pk_id,
            table_id=self.table_id,
            name="pk_bad",
            constraint_type=ConstraintType.PRIMARY_KEY,
            columns=("non_existent_column",),
            provenance=self.prov,
        )
        with self.assertRaises(ConstraintOwnershipError):
            reconstruct_primary_key(canonical_pk, self.table_id, self.columns)

    def test_invalid_constraint_type_raises(self) -> None:
        pk_id = compute_stable_object_id("constraint", "postgresql", (str(self.table_id), "c_bad"))
        bad_constraint = CanonicalConstraint(
            id=pk_id,
            table_id=self.table_id,
            name="c_bad",
            constraint_type=ConstraintType.UNIQUE,
            columns=("order_id",),
            provenance=self.prov,
        )
        with self.assertRaises(PrimaryKeyReconstructionError):
            reconstruct_primary_key(bad_constraint, self.table_id, self.columns)

    def test_empty_columns_raises(self) -> None:
        pk_id = compute_stable_object_id(
            "primary_key", "postgresql", (str(self.table_id), "pk_empty")
        )
        empty_pk = CanonicalConstraint(
            id=pk_id,
            table_id=self.table_id,
            name="pk_empty",
            constraint_type=ConstraintType.PRIMARY_KEY,
            columns=(),
            provenance=self.prov,
        )
        with self.assertRaises(PrimaryKeyReconstructionError):
            reconstruct_primary_key(empty_pk, self.table_id, self.columns)


if __name__ == "__main__":
    unittest.main()
