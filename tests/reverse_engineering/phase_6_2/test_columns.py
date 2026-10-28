"""Unit tests for column reconstruction in Phase 6.2."""

import unittest

from dera.metadata.enums import CanonicalTypeCategory, GenerationMode
from dera.metadata.identity import compute_stable_object_id
from dera.reverse_engineering.reconstruction.columns import (
    reconstruct_column,
    reconstruct_columns,
)
from dera.reverse_engineering.reconstruction.errors import InvalidColumnDefinitionError
from dera.reverse_engineering.reconstruction.models import (
    DefaultKind,
    NullabilityState,
)

from tests.reverse_engineering.phase_6_2.fixtures import (
    make_test_column,
)


class TestColumnReconstruction(unittest.TestCase):
    """Test column reconstruction, ordering, nullability, defaults, and identity."""

    def test_reconstruct_column_basic(self) -> None:
        col = make_test_column(
            table_id="tbl_1",
            name="user_id",
            ordinal=1,
            native_type="bigint",
            canonical_type=CanonicalTypeCategory.INTEGER,
            is_nullable=False,
            default_val="nextval('user_id_seq'::regclass)",
        )
        parent_id = compute_stable_object_id("table", "postgresql", ("public", "users"))
        reconstructed = reconstruct_column(col, parent_id, "postgresql")

        self.assertEqual(reconstructed.native_name, "user_id")
        self.assertEqual(reconstructed.ordinal_position, 1)
        self.assertEqual(reconstructed.native_type, "bigint")
        self.assertEqual(reconstructed.canonical_type, CanonicalTypeCategory.INTEGER)
        self.assertEqual(reconstructed.nullability, NullabilityState.NOT_NULLABLE)
        self.assertEqual(reconstructed.default_value.kind, DefaultKind.EXPRESSION)
        self.assertTrue(reconstructed.default_value.is_inert)
        self.assertTrue(reconstructed.identity.is_auto_increment)
        self.assertEqual(reconstructed.identity.strategy, "SEQUENCE")

    def test_reconstruct_column_nullability_states(self) -> None:
        parent_id = compute_stable_object_id("table", "postgresql", ("public", "demo"))
        c1 = make_test_column("t", "c1", 1, is_nullable=True)
        c2 = make_test_column("t", "c2", 2, is_nullable=False)
        c3 = make_test_column("t", "c3", 3, is_nullable=None)

        r1 = reconstruct_column(c1, parent_id, "postgresql")
        r2 = reconstruct_column(c2, parent_id, "postgresql")
        r3 = reconstruct_column(c3, parent_id, "postgresql")

        self.assertEqual(r1.nullability, NullabilityState.NULLABLE)
        self.assertEqual(r2.nullability, NullabilityState.NOT_NULLABLE)
        self.assertEqual(r3.nullability, NullabilityState.UNKNOWN)

    def test_reconstruct_generated_column(self) -> None:
        parent_id = compute_stable_object_id("table", "postgresql", ("public", "demo"))
        c = make_test_column(
            "t",
            "full_name",
            1,
            native_type="varchar(200)",
            canonical_type=CanonicalTypeCategory.TEXT,
            is_generated=True,
            gen_expr="first_name || ' ' || last_name",
        )
        r = reconstruct_column(c, parent_id, "postgresql")
        self.assertTrue(r.generated_column.is_generated)
        self.assertEqual(r.generated_column.expression, "first_name || ' ' || last_name")
        self.assertEqual(r.generated_column.generation_mode, GenerationMode.STORED)
        self.assertTrue(r.generated_column.is_stored)

    def test_reconstruct_columns_ordering(self) -> None:
        parent_id = compute_stable_object_id("table", "postgresql", ("public", "demo"))
        # Provided out-of-order ordinals
        c3 = make_test_column("t", "created_at", 3, "timestamp", CanonicalTypeCategory.TIMESTAMP)
        c1 = make_test_column("t", "id", 1, "integer", CanonicalTypeCategory.INTEGER)
        c2 = make_test_column("t", "name", 2, "text", CanonicalTypeCategory.TEXT)

        reconstructed = reconstruct_columns((c3, c1, c2), parent_id, "postgresql")
        self.assertEqual([c.native_name for c in reconstructed], ["id", "name", "created_at"])
        self.assertEqual([c.ordinal_position for c in reconstructed], [1, 2, 3])

    def test_invalid_ordinal_position_raises(self) -> None:
        parent_id = compute_stable_object_id("table", "postgresql", ("public", "demo"))
        bad_col = make_test_column("t", "bad", 0)  # 0 is invalid
        with self.assertRaises(InvalidColumnDefinitionError):
            reconstruct_column(bad_col, parent_id, "postgresql")

    def test_duplicate_column_name_raises(self) -> None:
        parent_id = compute_stable_object_id("table", "postgresql", ("public", "demo"))
        c1 = make_test_column("t", "code", 1)
        c2 = make_test_column("t", "code", 2)
        with self.assertRaises(InvalidColumnDefinitionError):
            reconstruct_columns((c1, c2), parent_id, "postgresql")


if __name__ == "__main__":
    unittest.main()
