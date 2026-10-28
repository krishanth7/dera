"""Unit tests for SchemaHierarchy navigation."""

from __future__ import annotations

import unittest

from dera.reverse_engineering.builder import SchemaBuilder

from tests.reverse_engineering.phase_6_1.fixtures import build_enterprise_fixture


class TestHierarchy(unittest.TestCase):
    """Test suite for hierarchical navigation over ObjectRegistry."""

    def setUp(self) -> None:
        self.enterprise_db = build_enterprise_fixture()
        self.schema = SchemaBuilder.from_canonical_database(self.enterprise_db)
        self.hierarchy = self.schema.hierarchy

    def test_database_and_namespaces_navigation(self) -> None:
        """Verify navigation from database to namespaces."""
        db = self.hierarchy.database(self.schema.database_id)
        self.assertEqual(db.name, "enterprise_db")

        ns_list = self.hierarchy.namespaces(self.schema.database_id)
        self.assertEqual(len(ns_list), 2)
        # Alphabetically sorted: 'analytics', then 'public'
        self.assertEqual(ns_list[0].name, "analytics")
        self.assertEqual(ns_list[1].name, "public")

    def test_namespace_to_tables_and_views(self) -> None:
        """Verify navigation from namespace to tables and views."""
        pub_ns = self.schema.database.get_namespace("public")
        self.assertIsNotNone(pub_ns)
        tables = self.hierarchy.tables(pub_ns.id)
        self.assertEqual(len(tables), 2)
        # Alphabetically sorted: 'organizations', 'users'
        self.assertEqual(tables[0].name, "organizations")
        self.assertEqual(tables[1].name, "users")

        analytics_ns = self.schema.database.get_namespace("analytics")
        self.assertIsNotNone(analytics_ns)
        views = self.hierarchy.views(analytics_ns.id)
        self.assertEqual(len(views), 1)
        self.assertEqual(views[0].name, "active_users_summary")

    def test_table_level_navigation(self) -> None:
        """Verify navigation from table to columns, constraints, indexes, triggers."""
        users_tbl = self.schema.find_table("public", "users")
        self.assertIsNotNone(users_tbl)

        # Columns sorted by ordinal position
        cols = self.hierarchy.columns(users_tbl.id)
        self.assertEqual(len(cols), 4)
        self.assertEqual([c.ordinal_position for c in cols], [1, 2, 3, 4])
        self.assertEqual([c.name for c in cols], ["user_id", "org_id", "email", "email_normalized"])

        # Primary Key
        pk = self.hierarchy.primary_key(users_tbl.id)
        self.assertIsNotNone(pk)
        self.assertEqual(pk.name, "pk_users")
        self.assertEqual(pk.columns, ("user_id",))

        # Unique constraints
        unqs = self.hierarchy.unique_constraints(users_tbl.id)
        self.assertEqual(len(unqs), 1)
        self.assertEqual(unqs[0].name, "unq_users_org_email")

        # Check constraints
        chks = self.hierarchy.check_constraints(users_tbl.id)
        self.assertEqual(len(chks), 1)
        self.assertEqual(chks[0].name, "chk_users_email_nonempty")

        # Foreign keys
        fks = self.hierarchy.foreign_keys(users_tbl.id)
        self.assertEqual(len(fks), 1)
        self.assertEqual(fks[0].name, "fk_users_org")

        # Indexes
        idxs = self.hierarchy.indexes(users_tbl.id)
        self.assertEqual(len(idxs), 1)
        self.assertEqual(idxs[0].name, "idx_users_email")

        # Triggers
        trgs = self.hierarchy.triggers(users_tbl.id)
        self.assertEqual(len(trgs), 1)
        self.assertEqual(trgs[0].name, "trg_users_audit")

    def test_cross_database_navigation(self) -> None:
        """Verify flat database-wide navigation methods."""
        all_tables = self.hierarchy.all_tables_in_database(self.schema.database_id)
        self.assertEqual(len(all_tables), 2)

        all_views = self.hierarchy.all_views_in_database(self.schema.database_id)
        self.assertEqual(len(all_views), 1)

        all_fks = self.hierarchy.all_foreign_keys_in_database(self.schema.database_id)
        self.assertEqual(len(all_fks), 1)


if __name__ == "__main__":
    unittest.main()
