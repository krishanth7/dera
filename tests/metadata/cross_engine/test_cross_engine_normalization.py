"""Tests for End-to-End Cross-Engine Normalization."""

from __future__ import annotations

import unittest

from dera.metadata.enums import (
    CanonicalTypeCategory,
)
from dera.metadata.normalization import MetadataNormalizer


class TestCrossEngineNormalization(unittest.TestCase):
    """Test suite executing normalization across PostgreSQL, SQLite, MySQL, and MariaDB."""

    def test_normalize_postgresql_report(self) -> None:
        """Verify normalization of a comprehensive PostgreSQL metadata report."""
        report = {
            "database_name": "app_db",
            "schemas": [{"schema_name": "public"}],
            "tables": [
                {
                    "schema_name": "public",
                    "table_name": "users",
                    "object_type": "TABLE",
                    "comment": "User accounts",
                }
            ],
            "columns": [
                {
                    "schema_name": "public",
                    "table_name": "users",
                    "column_name": "id",
                    "ordinal_position": 1,
                    "data_type": "bigint",
                    "is_nullable": False,
                },
                {
                    "schema_name": "public",
                    "table_name": "users",
                    "column_name": "email",
                    "ordinal_position": 2,
                    "data_type": "varchar(255)",
                    "is_nullable": False,
                },
                {
                    "schema_name": "public",
                    "table_name": "users",
                    "column_name": "metadata",
                    "ordinal_position": 3,
                    "data_type": "jsonb",
                    "is_nullable": True,
                },
            ],
            "primary_keys": [
                {
                    "schema_name": "public",
                    "table_name": "users",
                    "constraint_name": "pk_users",
                    "columns": ["id"],
                }
            ],
            "unique_constraints": [
                {
                    "schema_name": "public",
                    "table_name": "users",
                    "constraint_name": "uq_users_email",
                    "columns": ["email"],
                }
            ],
            "check_constraints": [],
            "foreign_keys": [],
            "indexes": [
                {
                    "schema_name": "public",
                    "table_name": "users",
                    "index_name": "idx_users_email",
                    "is_unique": True,
                    "is_primary": False,
                    "columns": ["email"],
                }
            ],
            "views": [
                {
                    "schema_name": "public",
                    "table_name": "active_users",
                    "view_definition": "SELECT * FROM users",
                    "is_updatable": False,
                }
            ],
            "triggers": [],
        }

        normalizer = MetadataNormalizer(
            engine="postgresql", database_name="app_db", server_version="16.2"
        )
        db = normalizer.normalize(report)

        self.assertEqual(db.engine, "postgresql")
        self.assertEqual(len(db.namespaces), 1)
        ns = db.namespaces[0]
        self.assertEqual(ns.name, "public")
        self.assertEqual(len(ns.tables), 1)
        self.assertEqual(len(ns.views), 1)

        tbl = ns.tables[0]
        self.assertEqual(tbl.name, "users")
        self.assertEqual(len(tbl.columns), 3)
        self.assertEqual(tbl.columns[0].canonical_type, CanonicalTypeCategory.INTEGER)
        self.assertEqual(tbl.columns[1].canonical_type, CanonicalTypeCategory.TEXT)
        self.assertEqual(tbl.columns[2].canonical_type, CanonicalTypeCategory.JSON)

        self.assertIsNotNone(tbl.primary_key)
        self.assertEqual(tbl.primary_key.name, "pk_users")
        self.assertEqual(len(tbl.unique_constraints), 1)
        self.assertEqual(len(tbl.indexes), 1)

    def test_normalize_sqlite_report(self) -> None:
        """Verify normalization of SQLite metadata with unnamed constraints and virtual columns."""
        report = {
            "database_name": "local.db",
            "schemas": [{"schema_name": "main"}],
            "tables": [{"schema_name": "main", "table_name": "items", "object_type": "TABLE"}],
            "columns": [
                {
                    "schema_name": "main",
                    "table_name": "items",
                    "column_name": "id",
                    "ordinal_position": 1,
                    "data_type": "INTEGER",
                    "is_nullable": False,
                },
                {
                    "schema_name": "main",
                    "table_name": "items",
                    "column_name": "name",
                    "ordinal_position": 2,
                    "data_type": "TEXT",
                    "is_nullable": False,
                },
                {
                    "schema_name": "main",
                    "table_name": "items",
                    "column_name": "slug",
                    "ordinal_position": 3,
                    "data_type": "TEXT",
                    "is_nullable": True,
                    "is_generated": True,
                    "extra": "virtual",
                },
            ],
            "primary_keys": [
                {
                    "schema_name": "main",
                    "table_name": "items",
                    "constraint_name": "pk_items",
                    "columns": ["id"],
                }
            ],
            "unique_constraints": [],
            "check_constraints": [
                {
                    "schema_name": "main",
                    "table_name": "items",
                    "constraint_name": "",
                    "columns": ["name"],
                    "check_clause": "length(name) > 0",
                }
            ],
            "foreign_keys": [],
            "indexes": [],
            "views": [],
            "triggers": [],
        }

        normalizer = MetadataNormalizer(
            engine="sqlite", database_name="local.db", server_version="3.45.0"
        )
        db = normalizer.normalize(report)

        tbl = db.namespaces[0].tables[0]
        self.assertEqual(len(tbl.columns), 3)
        slug_col = tbl.columns[2]
        self.assertTrue(slug_col.is_generated)

        # Unnamed check constraint should have synthetic name
        self.assertEqual(len(tbl.check_constraints), 1)
        chk = tbl.check_constraints[0]
        self.assertTrue(chk.is_synthetic_name)
        self.assertTrue(chk.name.startswith("_chk_items_"))

    def test_normalize_mysql_report(self) -> None:
        """Verify normalization of MySQL metadata with enums, sets, and boolean aliases."""
        report = {
            "database_name": "commerce",
            "schemas": [{"schema_name": "commerce"}],
            "tables": [{"schema_name": "commerce", "table_name": "orders", "object_type": "TABLE"}],
            "columns": [
                {
                    "schema_name": "commerce",
                    "table_name": "orders",
                    "column_name": "id",
                    "ordinal_position": 1,
                    "data_type": "bigint",
                    "is_nullable": False,
                },
                {
                    "schema_name": "commerce",
                    "table_name": "orders",
                    "column_name": "is_active",
                    "ordinal_position": 2,
                    "data_type": "tinyint",
                    "extra": "tinyint(1)",
                    "is_nullable": False,
                },
                {
                    "schema_name": "commerce",
                    "table_name": "orders",
                    "column_name": "status",
                    "ordinal_position": 3,
                    "data_type": "enum",
                    "is_nullable": False,
                },
            ],
            "primary_keys": [
                {
                    "schema_name": "commerce",
                    "table_name": "orders",
                    "constraint_name": "PRIMARY",
                    "columns": ["id"],
                }
            ],
            "unique_constraints": [],
            "check_constraints": [],
            "foreign_keys": [],
            "indexes": [],
            "views": [],
            "triggers": [],
        }

        normalizer = MetadataNormalizer(
            engine="mysql", database_name="commerce", server_version="8.0.36"
        )
        db = normalizer.normalize(report)

        tbl = db.namespaces[0].tables[0]
        self.assertEqual(tbl.columns[1].canonical_type, CanonicalTypeCategory.BOOLEAN)
        self.assertEqual(tbl.columns[2].canonical_type, CanonicalTypeCategory.ENUM)


if __name__ == "__main__":
    unittest.main()
