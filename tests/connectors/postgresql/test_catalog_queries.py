"""Tests for PostgreSQL system catalog queries, validation, and metadata extraction."""

import unittest
from unittest.mock import AsyncMock

from dera_connectors.engine import DatabaseEngine, DatabaseProvider
from dera_connectors.postgresql.catalog import (
    inspect_check_constraints,
    inspect_columns,
    inspect_foreign_keys,
    inspect_identity,
    inspect_indexes,
    inspect_primary_key,
    inspect_schemas,
    inspect_tables,
    inspect_unique_constraints,
    inspect_views,
)
from dera_connectors.postgresql.queries import (
    QUERY_CHECK_CONSTRAINTS,
    QUERY_COLUMNS,
    QUERY_FOREIGN_KEYS,
    QUERY_IDENTITY,
    QUERY_INDEXES,
    QUERY_PARTITIONS,
    QUERY_PRIMARY_KEY,
    QUERY_SCHEMAS,
    QUERY_SEQUENCES,
    QUERY_TABLES,
    QUERY_UNIQUE_CONSTRAINTS,
    QUERY_VIEWS,
)
from dera_connectors.security import validate_read_only_sql


class TestCatalogQueries(unittest.IsolatedAsyncioTestCase):
    """Verify system catalog queries and catalog parser functions."""

    def test_queries_are_strictly_read_only(self) -> None:
        """Verify all introspection SQL queries pass read-only query validation."""
        queries = [
            QUERY_IDENTITY,
            QUERY_SCHEMAS,
            QUERY_TABLES,
            QUERY_COLUMNS,
            QUERY_PRIMARY_KEY,
            QUERY_FOREIGN_KEYS,
            QUERY_UNIQUE_CONSTRAINTS,
            QUERY_CHECK_CONSTRAINTS,
            QUERY_INDEXES,
            QUERY_VIEWS,
            QUERY_SEQUENCES,
            QUERY_PARTITIONS,
        ]
        for query in queries:
            try:
                validate_read_only_sql(query)
            except Exception as exc:
                self.fail(f"Catalog query failed read-only check: {exc}")

    async def test_inspect_identity(self) -> None:
        """Verify server identity discovery extraction."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {
            "full_version": "PostgreSQL 16.2 on x86_64-pc-linux-gnu, compiled by gcc",
            "version_num": 160002,
            "current_database": "customer_db",
            "current_user": "analyst",
        }

        identity = await inspect_identity(mock_conn, provider=DatabaseProvider.GENERIC)
        self.assertEqual(identity.engine, DatabaseEngine.POSTGRESQL)
        self.assertEqual(identity.server_version, "PostgreSQL 16.2")
        self.assertEqual(identity.server_capability_hints["server_version_num"], 160002)
        self.assertEqual(identity.driver_version, "asyncpg")

    async def test_inspect_schemas(self) -> None:
        """Verify schema listing deterministic ordering."""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {"schema_name": "public", "comment": "Standard public schema"},
            {"schema_name": "analytics", "comment": "Data warehouse analytics schema"},
            {"schema_name": "auth", "comment": None},
        ]

        schemas = await inspect_schemas(mock_conn)
        names = [s.schema_name for s in schemas]
        self.assertEqual(names, ["analytics", "auth", "public"])
        self.assertEqual(schemas[0].comment, "Data warehouse analytics schema")

    async def test_inspect_tables(self) -> None:
        """Verify table listing deterministic ordering and object_type classification."""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {
                "schema_name": "public",
                "table_name": "users",
                "object_type": "TABLE",
                "comment": "User accounts",
                "is_unlogged": False,
                "is_partitioned": False,
            },
            {
                "schema_name": "analytics",
                "table_name": "events",
                "object_type": "PARTITIONED TABLE",
                "comment": "Time-series partitioned events",
                "is_unlogged": False,
                "is_partitioned": True,
            },
        ]

        tables = await inspect_tables(mock_conn)
        self.assertEqual(len(tables), 2)
        # Alphabetical by (schema_name, table_name)
        self.assertEqual(tables[0].schema_name, "analytics")
        self.assertEqual(tables[0].table_name, "events")
        self.assertEqual(tables[0].object_type, "PARTITIONED TABLE")
        self.assertTrue(tables[0].engine_specific["is_partitioned"])

        self.assertEqual(tables[1].schema_name, "public")
        self.assertEqual(tables[1].table_name, "users")

    async def test_inspect_columns(self) -> None:
        """Verify column inspection preserves ordinal ordering, nullability, and types."""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {
                "schema_name": "public",
                "table_name": "orders",
                "column_name": "id",
                "ordinal_position": 1,
                "data_type": "bigint",
                "is_nullable": False,
                "default_expression": "nextval('orders_id_seq'::regclass)",
                "is_identity": True,
                "is_generated": False,
                "generation_expression": None,
                "comment": "Primary identifier",
                "collation_name": None,
            },
            {
                "schema_name": "public",
                "table_name": "orders",
                "column_name": "total_amount",
                "ordinal_position": 2,
                "data_type": "numeric(12,2)",
                "is_nullable": False,
                "default_expression": "0.00",
                "is_identity": False,
                "is_generated": False,
                "generation_expression": None,
                "comment": None,
                "collation_name": None,
            },
        ]

        columns = await inspect_columns(mock_conn, schema="public", table="orders")
        self.assertEqual(len(columns), 2)
        self.assertEqual(columns[0].column_name, "id")
        self.assertEqual(columns[0].ordinal_position, 1)
        self.assertTrue(columns[0].is_identity)
        self.assertFalse(columns[0].is_nullable)

        self.assertEqual(columns[1].column_name, "total_amount")
        self.assertEqual(columns[1].data_type, "numeric(12,2)")

    async def test_inspect_primary_key(self) -> None:
        """Verify primary key constraint discovery."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {
            "constraint_name": "pk_orders",
            "schema_name": "public",
            "table_name": "orders",
            "column_names": ["tenant_id", "order_id"],
        }

        pk = await inspect_primary_key(mock_conn, schema="public", table="orders")
        self.assertIsNotNone(pk)
        self.assertEqual(pk.constraint_name, "pk_orders")
        self.assertEqual(pk.column_names, ["tenant_id", "order_id"])

    async def test_inspect_foreign_keys(self) -> None:
        """Verify foreign key relationship discovery."""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {
                "constraint_name": "fk_orders_user",
                "schema_name": "public",
                "table_name": "orders",
                "column_names": ["user_id"],
                "referenced_schema": "public",
                "referenced_table": "users",
                "referenced_columns": ["id"],
                "on_update": "CASCADE",
                "on_delete": "SET NULL",
            }
        ]

        fks = await inspect_foreign_keys(mock_conn, schema="public", table="orders")
        self.assertEqual(len(fks), 1)
        self.assertEqual(fks[0].constraint_name, "fk_orders_user")
        self.assertEqual(fks[0].referenced_table, "users")
        self.assertEqual(fks[0].on_delete, "SET NULL")

    async def test_inspect_unique_and_check_constraints(self) -> None:
        """Verify unique and check constraint parsing."""
        mock_conn = AsyncMock()
        mock_conn.fetch.side_effect = [
            [
                {
                    "constraint_name": "uq_user_email",
                    "schema_name": "public",
                    "table_name": "users",
                    "column_names": ["email"],
                }
            ],
            [
                {
                    "constraint_name": "chk_positive_price",
                    "schema_name": "public",
                    "table_name": "orders",
                    "check_clause": "CHECK ((total_amount >= (0)::numeric))",
                }
            ],
        ]

        uniques = await inspect_unique_constraints(mock_conn, schema="public", table="users")
        self.assertEqual(len(uniques), 1)
        self.assertEqual(uniques[0].constraint_name, "uq_user_email")

        checks = await inspect_check_constraints(mock_conn, schema="public", table="orders")
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].constraint_name, "chk_positive_price")
        self.assertIn("total_amount", checks[0].check_clause)

    async def test_inspect_indexes(self) -> None:
        """Verify secondary index parsing with partial predicates and access methods."""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {
                "index_name": "idx_orders_created",
                "schema_name": "public",
                "table_name": "orders",
                "column_names": ["created_at"],
                "is_unique": False,
                "is_primary": False,
                "index_type": "btree",
                "predicate": None,
            },
            {
                "index_name": "idx_active_users",
                "schema_name": "public",
                "table_name": "users",
                "column_names": ["email"],
                "is_unique": True,
                "is_primary": False,
                "index_type": "btree",
                "predicate": "(status = 'active')",
            },
        ]

        indexes = await inspect_indexes(mock_conn, schema="public", table="orders")
        self.assertEqual(len(indexes), 2)
        self.assertEqual(indexes[0].index_name, "idx_active_users")
        self.assertEqual(indexes[0].predicate, "(status = 'active')")
        self.assertEqual(indexes[0].index_type, "BTREE")

    async def test_inspect_views(self) -> None:
        """Verify view and materialized view discovery."""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {
                "schema_name": "public",
                "view_name": "v_daily_sales",
                "is_materialized": False,
                "view_definition": "SELECT date, sum(amount) FROM sales GROUP BY date;",
                "comment": "Daily aggregated sales report",
            },
            {
                "schema_name": "analytics",
                "view_name": "mv_customer_metrics",
                "is_materialized": True,
                "view_definition": "SELECT customer_id, count(*) FROM orders GROUP BY customer_id;",
                "comment": "Materialized customer metrics cache",
            },
        ]

        views = await inspect_views(mock_conn)
        self.assertEqual(len(views), 2)
        self.assertEqual(views[0].view_name, "mv_customer_metrics")
        self.assertTrue(views[0].is_materialized)
        self.assertEqual(views[1].view_name, "v_daily_sales")
        self.assertFalse(views[1].is_materialized)


if __name__ == "__main__":
    unittest.main()
