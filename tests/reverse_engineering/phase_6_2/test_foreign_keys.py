"""Unit tests for foreign key reconstruction in Phase 6.2."""

import unittest

from dera.metadata.enums import ForeignKeyAction
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.models import CanonicalForeignKey, CanonicalTable
from dera.reverse_engineering.reconstruction.columns import reconstruct_columns
from dera.reverse_engineering.reconstruction.errors import (
    ConstraintOwnershipError,
    ForeignKeyReconstructionError,
)
from dera.reverse_engineering.reconstruction.foreign_keys import reconstruct_foreign_key
from dera.reverse_engineering.references import ResolutionStatus
from dera.reverse_engineering.registry import ObjectRegistry
from tests.reverse_engineering.phase_6_2.fixtures import (
    make_test_column,
    make_test_provenance,
)


class TestForeignKeyReconstruction(unittest.TestCase):
    """Test foreign key reconstruction, composite matching, and registry resolution."""

    def setUp(self) -> None:
        self.prov = make_test_provenance("postgresql")
        self.src_id = compute_stable_object_id("table", "postgresql", ("public", "orders"))
        c1 = make_test_column(str(self.src_id), "tenant_id", 1, "uuid")
        c2 = make_test_column(str(self.src_id), "cust_id", 2, "bigint")
        self.columns = reconstruct_columns((c1, c2), self.src_id, "postgresql")

    def test_reconstruct_foreign_key_basic(self) -> None:
        fk_id = compute_stable_object_id("foreign_key", "postgresql", (str(self.src_id), "fk_orders_cust"))
        canonical_fk = CanonicalForeignKey(
            id=fk_id,
            table_id=self.src_id,
            name="fk_orders_cust",
            columns=("cust_id",),
            referenced_schema="public",
            referenced_table="customers",
            referenced_columns=("id",),
            on_update=ForeignKeyAction.CASCADE,
            on_delete=ForeignKeyAction.RESTRICT,
            provenance=self.prov,
        )
        fk = reconstruct_foreign_key(canonical_fk, self.src_id, "public", self.columns)
        self.assertEqual(fk.native_name, "fk_orders_cust")
        self.assertFalse(fk.is_composite)
        self.assertFalse(fk.is_cross_namespace)
        self.assertEqual(fk.source_column_names, ("cust_id",))
        self.assertEqual(fk.referenced_column_names, ("id",))
        self.assertEqual(fk.on_update, ForeignKeyAction.CASCADE)
        self.assertEqual(fk.on_delete, ForeignKeyAction.RESTRICT)

    def test_composite_foreign_key(self) -> None:
        fk_id = compute_stable_object_id("foreign_key", "postgresql", (str(self.src_id), "fk_orders_tenant_cust"))
        canonical_fk = CanonicalForeignKey(
            id=fk_id,
            table_id=self.src_id,
            name="fk_orders_tenant_cust",
            columns=("tenant_id", "cust_id"),
            referenced_schema="public",
            referenced_table="customers",
            referenced_columns=("tenant_id", "id"),
            on_update=ForeignKeyAction.NO_ACTION,
            on_delete=ForeignKeyAction.CASCADE,
            provenance=self.prov,
        )
        fk = reconstruct_foreign_key(canonical_fk, self.src_id, "public", self.columns)
        self.assertTrue(fk.is_composite)
        self.assertEqual(fk.source_column_names, ("tenant_id", "cust_id"))
        self.assertEqual(fk.referenced_column_names, ("tenant_id", "id"))

    def test_column_count_mismatch_raises(self) -> None:
        fk_id = compute_stable_object_id("foreign_key", "postgresql", (str(self.src_id), "fk_bad"))
        canonical_fk = CanonicalForeignKey(
            id=fk_id,
            table_id=self.src_id,
            name="fk_bad",
            columns=("tenant_id", "cust_id"),
            referenced_schema="public",
            referenced_table="customers",
            referenced_columns=("id",),  # 2 vs 1
            on_update=ForeignKeyAction.NO_ACTION,
            on_delete=ForeignKeyAction.CASCADE,
            provenance=self.prov,
        )
        with self.assertRaises(ForeignKeyReconstructionError):
            reconstruct_foreign_key(canonical_fk, self.src_id, "public", self.columns)

    def test_source_column_not_in_table_raises(self) -> None:
        fk_id = compute_stable_object_id("foreign_key", "postgresql", (str(self.src_id), "fk_bad_col"))
        canonical_fk = CanonicalForeignKey(
            id=fk_id,
            table_id=self.src_id,
            name="fk_bad_col",
            columns=("ghost_column",),
            referenced_schema="public",
            referenced_table="customers",
            referenced_columns=("id",),
            on_update=ForeignKeyAction.NO_ACTION,
            on_delete=ForeignKeyAction.NO_ACTION,
            provenance=self.prov,
        )
        with self.assertRaises(ConstraintOwnershipError):
            reconstruct_foreign_key(canonical_fk, self.src_id, "public", self.columns)

    def test_cross_namespace_foreign_key(self) -> None:
        fk_id = compute_stable_object_id("foreign_key", "postgresql", (str(self.src_id), "fk_cross_ns"))
        canonical_fk = CanonicalForeignKey(
            id=fk_id,
            table_id=self.src_id,
            name="fk_cross_ns",
            columns=("cust_id",),
            referenced_schema="auth",  # different from source "public"
            referenced_table="users",
            referenced_columns=("id",),
            on_update=ForeignKeyAction.CASCADE,
            on_delete=ForeignKeyAction.SET_NULL,
            provenance=self.prov,
        )
        fk = reconstruct_foreign_key(canonical_fk, self.src_id, "public", self.columns)
        self.assertTrue(fk.is_cross_namespace)
        self.assertEqual(fk.referenced_namespace, "auth")

    def test_registry_resolution(self) -> None:
        registry = ObjectRegistry(workspace_id="ws-test")
        target_id = compute_stable_object_id("table", "postgresql", ("public", "customers"), "ws-test")
        col_id = make_test_column(str(target_id), "id", 1, workspace_id="ws-test")
        target_table = CanonicalTable(
            id=target_id,
            namespace_id=compute_stable_object_id("namespace", "postgresql", ("public",), "ws-test"),
            schema_name="public",
            name="customers",
            columns=(col_id,),
            provenance=self.prov,
        )
        registry.register(target_table)

        fk_id = compute_stable_object_id("foreign_key", "postgresql", (str(self.src_id), "fk_resolved"))
        canonical_fk = CanonicalForeignKey(
            id=fk_id,
            table_id=self.src_id,
            name="fk_resolved",
            columns=("cust_id",),
            referenced_schema="public",
            referenced_table="customers",
            referenced_columns=("id",),
            on_update=ForeignKeyAction.CASCADE,
            on_delete=ForeignKeyAction.CASCADE,
            provenance=self.prov,
        )

        fk = reconstruct_foreign_key(canonical_fk, self.src_id, "public", self.columns, registry=registry)
        self.assertEqual(fk.resolution_status, ResolutionStatus.RESOLVED)
        self.assertEqual(fk.referenced_table_id, target_id)


if __name__ == "__main__":
    unittest.main()
