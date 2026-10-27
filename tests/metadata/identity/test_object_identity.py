"""Tests for Stable Object Identity Generation."""

from __future__ import annotations

import unittest

from dera.metadata.enums import ObjectKind
from dera.metadata.identity import (
    compute_stable_object_id,
    generate_unnamed_constraint_name,
)


class TestObjectIdentity(unittest.TestCase):
    """Test suite verifying properties of deterministic ObjectId formulation."""

    def test_identity_determinism(self) -> None:
        """Verify identical parameters always produce identical ID string."""
        id1 = compute_stable_object_id("postgresql", ObjectKind.TABLE, "users", namespace="public")
        id2 = compute_stable_object_id("postgresql", ObjectKind.TABLE, "users", namespace="public")
        self.assertEqual(id1, id2)
        self.assertTrue(id1.startswith("dera:table:"))
        self.assertEqual(len(id1), len("dera:table:") + 24)

    def test_distinct_namespaces_produce_distinct_ids(self) -> None:
        """Verify same table name in different schemas yields different IDs."""
        id_public = compute_stable_object_id(
            "postgresql", ObjectKind.TABLE, "users", namespace="public"
        )
        id_audit = compute_stable_object_id(
            "postgresql", ObjectKind.TABLE, "users", namespace="audit"
        )
        self.assertNotEqual(id_public, id_audit)

    def test_distinct_object_kinds_produce_distinct_ids(self) -> None:
        """Verify table and view with identical names produce different IDs."""
        tbl_id = compute_stable_object_id(
            "postgresql", ObjectKind.TABLE, "active_users", namespace="public"
        )
        view_id = compute_stable_object_id(
            "postgresql", ObjectKind.VIEW, "active_users", namespace="public"
        )
        self.assertNotEqual(tbl_id, view_id)

    def test_distinct_parents_produce_distinct_child_ids(self) -> None:
        """Verify same column name under different parent tables yields different IDs."""
        col_users = compute_stable_object_id(
            "postgresql", ObjectKind.COLUMN, "created_at", parent_id="tbl_users"
        )
        col_orders = compute_stable_object_id(
            "postgresql", ObjectKind.COLUMN, "created_at", parent_id="tbl_orders"
        )
        self.assertNotEqual(col_users, col_orders)

    def test_delimiter_collision_resistance(self) -> None:
        """Verify length-prefixed framing prevents delimiter concatenation ambiguity."""
        # e.g., name='ab' + term='c' vs name='a' + term='bc'
        id1 = compute_stable_object_id("postgresql", ObjectKind.INDEX, "idx", terms=("ab", "c"))
        id2 = compute_stable_object_id("postgresql", ObjectKind.INDEX, "idx", terms=("a", "bc"))
        self.assertNotEqual(id1, id2)

    def test_workspace_isolation_in_identity(self) -> None:
        """Verify different workspace scopes produce distinct identities."""
        id_ws1 = compute_stable_object_id(
            "postgresql", ObjectKind.TABLE, "accounts", workspace_id="ws_corp_a"
        )
        id_ws2 = compute_stable_object_id(
            "postgresql", ObjectKind.TABLE, "accounts", workspace_id="ws_corp_b"
        )
        self.assertNotEqual(id_ws1, id_ws2)

    def test_unnamed_constraint_surrogate_generation(self) -> None:
        """Verify deterministic generation of unnamed constraint surrogate names."""
        surrogate = generate_unnamed_constraint_name(
            table_name="orders",
            constraint_kind="check",
            columns=["amount", "status"],
        )
        self.assertEqual(surrogate, "_chk_orders_amount_status")


if __name__ == "__main__":
    unittest.main()
