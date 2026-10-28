"""Unit tests for unique constraint reconstruction in Phase 6.2."""

import unittest

from dera.metadata.enums import ConstraintType
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.models import CanonicalConstraint
from dera.reverse_engineering.reconstruction.columns import reconstruct_columns
from dera.reverse_engineering.reconstruction.errors import (
    ConstraintOwnershipError,
    UniqueConstraintReconstructionError,
)
from dera.reverse_engineering.reconstruction.unique_constraints import (
    reconstruct_unique_constraint,
    reconstruct_unique_constraints,
)

from tests.reverse_engineering.phase_6_2.fixtures import (
    make_test_column,
    make_test_provenance,
)


class TestUniqueConstraintReconstruction(unittest.TestCase):
    """Test unique constraint reconstruction and NULL semantics."""

    def setUp(self) -> None:
        self.prov = make_test_provenance("postgresql")
        self.table_id = compute_stable_object_id("table", "postgresql", ("public", "accounts"))
        c1 = make_test_column(str(self.table_id), "org_id", 1, "uuid")
        c2 = make_test_column(str(self.table_id), "email", 2, "varchar")
        self.columns = reconstruct_columns((c1, c2), self.table_id, "postgresql")

    def test_single_column_unique_constraint(self) -> None:
        uq_id = compute_stable_object_id(
            "unique_constraint", "postgresql", (str(self.table_id), "uq_email")
        )
        canonical_uq = CanonicalConstraint(
            id=uq_id,
            table_id=self.table_id,
            name="uq_email",
            constraint_type=ConstraintType.UNIQUE,
            columns=("email",),
            provenance=self.prov,
        )
        uq = reconstruct_unique_constraint(canonical_uq, self.table_id, self.columns)
        self.assertFalse(uq.is_composite)
        self.assertEqual(uq.column_names, ("email",))

    def test_composite_unique_constraint_order(self) -> None:
        uq_id = compute_stable_object_id(
            "unique_constraint", "postgresql", (str(self.table_id), "uq_org_email")
        )
        canonical_uq = CanonicalConstraint(
            id=uq_id,
            table_id=self.table_id,
            name="uq_org_email",
            constraint_type=ConstraintType.UNIQUE,
            columns=("org_id", "email"),
            extra_metadata={"null_distinct": True},
            provenance=self.prov,
        )
        uq = reconstruct_unique_constraint(canonical_uq, self.table_id, self.columns)
        self.assertTrue(uq.is_composite)
        self.assertEqual(uq.column_names, ("org_id", "email"))
        self.assertTrue(uq.null_distinct)

    def test_missing_column_raises(self) -> None:
        uq_id = compute_stable_object_id(
            "unique_constraint", "postgresql", (str(self.table_id), "uq_bad")
        )
        canonical_uq = CanonicalConstraint(
            id=uq_id,
            table_id=self.table_id,
            name="uq_bad",
            constraint_type=ConstraintType.UNIQUE,
            columns=("missing_column",),
            provenance=self.prov,
        )
        with self.assertRaises(ConstraintOwnershipError):
            reconstruct_unique_constraint(canonical_uq, self.table_id, self.columns)

    def test_invalid_constraint_type_raises(self) -> None:
        c_id = compute_stable_object_id(
            "constraint", "postgresql", (str(self.table_id), "c_not_uq")
        )
        canonical_c = CanonicalConstraint(
            id=c_id,
            table_id=self.table_id,
            name="c_not_uq",
            constraint_type=ConstraintType.PRIMARY_KEY,
            columns=("email",),
            provenance=self.prov,
        )
        with self.assertRaises(UniqueConstraintReconstructionError):
            reconstruct_unique_constraint(canonical_c, self.table_id, self.columns)

    def test_reconstruct_multiple_unique_constraints_sorted(self) -> None:
        uq1_id = compute_stable_object_id(
            "unique_constraint", "postgresql", (str(self.table_id), "uq_z")
        )
        uq2_id = compute_stable_object_id(
            "unique_constraint", "postgresql", (str(self.table_id), "uq_a")
        )
        c1 = CanonicalConstraint(
            id=uq1_id,
            table_id=self.table_id,
            name="uq_z",
            constraint_type=ConstraintType.UNIQUE,
            columns=("email",),
            provenance=self.prov,
        )
        c2 = CanonicalConstraint(
            id=uq2_id,
            table_id=self.table_id,
            name="uq_a",
            constraint_type=ConstraintType.UNIQUE,
            columns=("org_id",),
            provenance=self.prov,
        )

        reconstructed = reconstruct_unique_constraints((c1, c2), self.table_id, self.columns)
        self.assertEqual([u.native_name for u in reconstructed], ["uq_a", "uq_z"])


if __name__ == "__main__":
    unittest.main()
