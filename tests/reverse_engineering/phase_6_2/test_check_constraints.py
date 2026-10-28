"""Unit tests for check constraint reconstruction in Phase 6.2."""

import unittest

from dera.metadata.enums import ConstraintType
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.models import CanonicalConstraint
from dera.reverse_engineering.reconstruction.check_constraints import (
    reconstruct_check_constraint,
    reconstruct_check_constraints,
)
from dera.reverse_engineering.reconstruction.errors import CheckConstraintReconstructionError
from dera.reverse_engineering.reconstruction.models import (
    ConstraintEnforcementStatus,
    ConstraintValidationStatus,
)
from tests.reverse_engineering.phase_6_2.fixtures import make_test_provenance


class TestCheckConstraintReconstruction(unittest.TestCase):
    """Test check constraint reconstruction, inert expressions, and validation states."""

    def setUp(self) -> None:
        self.prov = make_test_provenance("postgresql")
        self.table_id = compute_stable_object_id("table", "postgresql", ("public", "products"))

    def test_reconstruct_check_constraint_basic(self) -> None:
        ck_id = compute_stable_object_id("check_constraint", "postgresql", (str(self.table_id), "ck_price_positive"))
        c = CanonicalConstraint(
            id=ck_id,
            table_id=self.table_id,
            name="ck_price_positive",
            constraint_type=ConstraintType.CHECK,
            expression="price > 0",
            extra_metadata={"is_enforced": True, "is_validated": True},
            provenance=self.prov,
        )
        ck = reconstruct_check_constraint(c, self.table_id)
        self.assertEqual(ck.native_name, "ck_price_positive")
        self.assertEqual(ck.expression, "price > 0")
        self.assertEqual(ck.enforcement_status, ConstraintEnforcementStatus.ENFORCED)
        self.assertEqual(ck.validation_status, ConstraintValidationStatus.VALIDATED)

    def test_missing_expression_raises(self) -> None:
        ck_id = compute_stable_object_id("check_constraint", "postgresql", (str(self.table_id), "ck_empty"))
        c = CanonicalConstraint(
            id=ck_id,
            table_id=self.table_id,
            name="ck_empty",
            constraint_type=ConstraintType.CHECK,
            expression="",
            provenance=self.prov,
        )
        with self.assertRaises(CheckConstraintReconstructionError):
            reconstruct_check_constraint(c, self.table_id)

    def test_reconstruct_multiple_checks_sorted(self) -> None:
        c1 = CanonicalConstraint(
            id=compute_stable_object_id("check_constraint", "postgresql", (str(self.table_id), "ck_z")),
            table_id=self.table_id,
            name="ck_z",
            constraint_type=ConstraintType.CHECK,
            expression="z > 0",
            provenance=self.prov,
        )
        c2 = CanonicalConstraint(
            id=compute_stable_object_id("check_constraint", "postgresql", (str(self.table_id), "ck_a")),
            table_id=self.table_id,
            name="ck_a",
            constraint_type=ConstraintType.CHECK,
            expression="a > 0",
            provenance=self.prov,
        )
        reconstructed = reconstruct_check_constraints((c1, c2), self.table_id)
        self.assertEqual([ck.native_name for ck in reconstructed], ["ck_a", "ck_z"])


if __name__ == "__main__":
    unittest.main()
