"""Unit tests for DERA canonical models, dependency graph, and diagnostics.

Deterministic validation tests.
Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from datetime import datetime, timezone
import unittest

from dera.models import (
    DatabaseColumn,
    DatabaseTable,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    SchemaSnapshot,
    TableIndex,
)
from dera.graph import build_dependency_graph, compute_topological_sort
from dera.diagnostics import run_all_diagnostics, RuleSeverity


class TestDeraCore(unittest.TestCase):
    def test_schema_model_creation_and_fingerprint(self) -> None:
        users_table = DatabaseTable(
            schema="public",
            name="users",
            columns=(
                DatabaseColumn(name="id", data_type="BIGINT", is_nullable=False),
                DatabaseColumn(name="email", data_type="VARCHAR(255)", is_nullable=False),
            ),
            primary_key=PrimaryKeyConstraint(name="pk_users", columns=("id",)),
            indexes=(TableIndex(name="idx_users_email", columns=("email",), is_unique=True),),
        )

        orders_table = DatabaseTable(
            schema="public",
            name="orders",
            columns=(
                DatabaseColumn(name="id", data_type="BIGINT", is_nullable=False),
                DatabaseColumn(name="user_id", data_type="BIGINT", is_nullable=False),
            ),
            primary_key=PrimaryKeyConstraint(name="pk_orders", columns=("id",)),
            foreign_keys=(
                ForeignKeyConstraint(
                    name="fk_orders_user",
                    source_columns=("user_id",),
                    target_schema="public",
                    target_table="users",
                    target_columns=("id",),
                ),
            ),
        )

        snapshot = SchemaSnapshot(
            database_name="production_db",
            engine="postgresql",
            tables=(users_table, orders_table),
            created_at=datetime.now(timezone.utc),
        )

        self.assertEqual(len(snapshot.tables), 2)
        self.assertIsNotNone(users_table.primary_key)
        self.assertEqual(orders_table.foreign_keys[0].target_table, "users")

        # Test deterministic fingerprinting
        hash1 = snapshot.compute_hash()
        hash2 = snapshot.compute_hash()
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA-256 hex string

    def test_dependency_graph_and_topological_sort(self) -> None:
        users_table = DatabaseTable(
            schema="public",
            name="users",
            columns=(DatabaseColumn(name="id", data_type="BIGINT", is_nullable=False),),
            primary_key=PrimaryKeyConstraint(name="pk_users", columns=("id",)),
        )

        orders_table = DatabaseTable(
            schema="public",
            name="orders",
            columns=(DatabaseColumn(name="user_id", data_type="BIGINT", is_nullable=False),),
            foreign_keys=(
                ForeignKeyConstraint(
                    name="fk_orders_user",
                    source_columns=("user_id",),
                    target_schema="public",
                    target_table="users",
                    target_columns=("id",),
                ),
            ),
        )

        tables = (users_table, orders_table)
        graph = build_dependency_graph(tables)
        self.assertIn("public.orders", graph["public.users"])

        order = compute_topological_sort(tables)
        # Order resolves dependencies: users must be created before orders
        self.assertEqual(order, ["public.users", "public.orders"])

    def test_diagnostics_unindexed_foreign_key_and_missing_pk(self) -> None:
        orders_table = DatabaseTable(
            schema="public",
            name="orders",
            columns=(DatabaseColumn(name="user_id", data_type="BIGINT", is_nullable=False),),
            foreign_keys=(
                ForeignKeyConstraint(
                    name="fk_orders_user",
                    source_columns=("user_id",),
                    target_schema="public",
                    target_table="users",
                    target_columns=("id",),
                ),
            ),
            indexes=(),  # Missing index on user_id
        )

        findings = run_all_diagnostics([orders_table])
        rule_ids = [f.rule_id for f in findings]

        self.assertIn("RULE-INT-001", rule_ids)   # Missing primary key
        self.assertIn("RULE-PERF-002", rule_ids)  # Unindexed foreign key

        # Verify remediation DDL is present
        remediations = [f.remediation_ddl for f in findings if f.remediation_ddl]
        self.assertTrue(any("PRIMARY KEY" in r for r in remediations))
        self.assertTrue(any("CREATE INDEX" in r for r in remediations))


if __name__ == "__main__":
    unittest.main()
