"""Live PostgreSQL integration tests against real disposable database instance.

Executes end-to-end introspection against real PostgreSQL (e.g. CI service container)
covering multiple schemas, composite keys, check constraints, partial indexes,
views, materialized views, sequences, partitions, unicode identifiers, and read-only checks.
"""

import os
import unittest

from dera_connectors.configuration import TLSSettings
from dera_connectors.engine import DatabaseEngine
from dera_connectors.postgresql.adapter import PostgresConnector
from dera_connectors.postgresql.configuration import PostgresConnectorConfig
from pydantic import SecretStr

# Environment configuration for live testbed
POSTGRES_HOST = os.getenv("DERA_TEST_POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = int(os.getenv("DERA_TEST_POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("DERA_TEST_POSTGRES_DB", "dera_test_db")
POSTGRES_USER = os.getenv("DERA_TEST_POSTGRES_USER", "dera_test_user")
POSTGRES_PASSWORD = os.getenv("DERA_TEST_POSTGRES_PASSWORD", "dera_ephemeral_test_password")

FIXTURE_SCHEMA = "dera_phase_5_2_test"

SCHEMA_FIXTURE_SQL = f"""
CREATE SCHEMA IF NOT EXISTS {FIXTURE_SCHEMA};

-- Sequence
CREATE SEQUENCE IF NOT EXISTS {FIXTURE_SCHEMA}.order_seq START 100 INCREMENT 1;

-- Users table with comments, unique constraint, and partial index
CREATE TABLE IF NOT EXISTS {FIXTURE_SCHEMA}.users (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_users_email UNIQUE (email)
);
COMMENT ON TABLE {FIXTURE_SCHEMA}.users IS 'Registered application users';
COMMENT ON COLUMN {FIXTURE_SCHEMA}.users.email IS 'Unique contact email address';

CREATE INDEX IF NOT EXISTS idx_users_active_email
ON {FIXTURE_SCHEMA}.users (email)
WHERE status = 'active';

-- Orders table with composite primary key and check constraint
CREATE TABLE IF NOT EXISTS {FIXTURE_SCHEMA}.orders (
    tenant_id BIGINT NOT NULL,
    order_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    CONSTRAINT pk_orders PRIMARY KEY (tenant_id, order_id),
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES {FIXTURE_SCHEMA}.users (id) ON DELETE CASCADE,
    CONSTRAINT chk_orders_amount_positive CHECK (total_amount >= 0)
);

-- Mixed-case and unicode table
CREATE TABLE IF NOT EXISTS {FIXTURE_SCHEMA}."Special_Unicode_Café" (
    "Item_ID" INT PRIMARY KEY,
    "Price_€" NUMERIC(8, 2) NOT NULL
);

-- Views and Materialized Views
CREATE OR REPLACE VIEW {FIXTURE_SCHEMA}.v_order_summary AS
SELECT user_id, COUNT(*) AS order_count, SUM(total_amount) AS total_spent
FROM {FIXTURE_SCHEMA}.orders
GROUP BY user_id;

DROP MATERIALIZED VIEW IF EXISTS {FIXTURE_SCHEMA}.mv_active_user_stats;
CREATE MATERIALIZED VIEW {FIXTURE_SCHEMA}.mv_active_user_stats AS
SELECT status, COUNT(*) AS count
FROM {FIXTURE_SCHEMA}.users
GROUP BY status;

-- Partitioned Table
CREATE TABLE IF NOT EXISTS {FIXTURE_SCHEMA}.measurements (
    sensor_id INT NOT NULL,
    recorded_at DATE NOT NULL,
    val NUMERIC(8, 2)
) PARTITION BY RANGE (recorded_at);

CREATE TABLE IF NOT EXISTS {FIXTURE_SCHEMA}.measurements_2026
PARTITION OF {FIXTURE_SCHEMA}.measurements
FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
"""

TEARDOWN_SQL = f"DROP SCHEMA IF EXISTS {FIXTURE_SCHEMA} CASCADE;"


class TestPostgresLiveIntegration(unittest.IsolatedAsyncioTestCase):
    """End-to-end integration tests executing against real disposable PostgreSQL instance."""

    _server_available: bool = False

    @classmethod
    def setUpClass(cls) -> None:
        """Probe if live PostgreSQL instance is available on target host and port."""
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        try:
            res = s.connect_ex((POSTGRES_HOST, POSTGRES_PORT))
            cls._server_available = res == 0
        except Exception:
            cls._server_available = False
        finally:
            s.close()

    async def asyncSetUp(self) -> None:
        """Skip test if no live PostgreSQL server is reachable."""
        if not self._server_available:
            self.skipTest(
                f"No live PostgreSQL database reachable at {POSTGRES_HOST}:{POSTGRES_PORT}. "
                "Skipping live integration tests (enabled in CI service containers)."
            )

        # Setup disposable test schema using a privileged raw asyncpg connection
        import asyncpg

        conn = await asyncpg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            timeout=5.0,
        )
        try:
            await conn.execute(SCHEMA_FIXTURE_SQL)
        finally:
            await conn.close()

    async def asyncTearDown(self) -> None:
        """Clean up disposable test schema."""
        if self._server_available:
            try:
                import asyncpg

                conn = await asyncpg.connect(
                    host=POSTGRES_HOST,
                    port=POSTGRES_PORT,
                    database=POSTGRES_DB,
                    user=POSTGRES_USER,
                    password=POSTGRES_PASSWORD,
                    timeout=5.0,
                )
                try:
                    await conn.execute(TEARDOWN_SQL)
                finally:
                    await conn.close()
            except Exception:
                pass

    def _get_test_connector(self) -> PostgresConnector:
        ssl_mode = os.getenv("DERA_TEST_POSTGRES_SSL", "disable")
        config = PostgresConnectorConfig(
            database=POSTGRES_DB,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            username=POSTGRES_USER,
            password=SecretStr(POSTGRES_PASSWORD),
            tls=TLSSettings(ssl_mode=ssl_mode),
        )
        return PostgresConnector(config=config, allow_loopback=True)

    async def test_live_full_catalog_introspection(self) -> None:
        """Verify full metadata inspection on real PostgreSQL database."""
        async with self._get_test_connector() as conn:
            # 1. Identity & capabilities
            identity = await conn.get_identity()
            self.assertEqual(identity.engine, DatabaseEngine.POSTGRESQL)
            self.assertIn("PostgreSQL", identity.server_version or "")
            self.assertGreater(
                identity.server_capability_hints.get("server_version_num", 0),
                100000,
            )

            caps = await conn.get_capabilities()
            self.assertEqual(caps.engine, DatabaseEngine.POSTGRESQL)

            # 2. Schemas
            schemas = await conn.list_schemas()
            schema_names = [s.schema_name for s in schemas]
            self.assertIn(FIXTURE_SCHEMA, schema_names)

            # 3. Tables
            tables = await conn.list_tables(schema=FIXTURE_SCHEMA)
            table_names = [t.table_name for t in tables]
            self.assertIn("users", table_names)
            self.assertIn("orders", table_names)
            self.assertIn("Special_Unicode_Café", table_names)
            self.assertIn("measurements", table_names)

            # 4. Columns & Comments
            columns = await conn.list_columns(schema=FIXTURE_SCHEMA, table="users")
            col_map = {c.column_name: c for c in columns}
            self.assertIn("id", col_map)
            self.assertIn("email", col_map)
            self.assertEqual(col_map["email"].comment, "Unique contact email address")
            self.assertFalse(col_map["email"].is_nullable)

            # 5. Primary Keys (Composite)
            pk = await conn.get_primary_key(schema=FIXTURE_SCHEMA, table="orders")
            self.assertIsNotNone(pk)
            self.assertEqual(pk.constraint_name, "pk_orders")
            self.assertEqual(pk.column_names, ["tenant_id", "order_id"])

            # 6. Foreign Keys
            fks = await conn.list_foreign_keys(schema=FIXTURE_SCHEMA, table="orders")
            self.assertEqual(len(fks), 1)
            self.assertEqual(fks[0].referenced_table, "users")
            self.assertEqual(fks[0].column_names, ["user_id"])
            self.assertEqual(fks[0].on_delete, "CASCADE")

            # 7. Unique & Check Constraints
            uniques = await conn.list_unique_constraints(schema=FIXTURE_SCHEMA, table="users")
            self.assertEqual(len(uniques), 1)
            self.assertEqual(uniques[0].column_names, ["email"])

            checks = await conn.list_check_constraints(schema=FIXTURE_SCHEMA, table="orders")
            self.assertEqual(len(checks), 1)
            self.assertIn("total_amount", checks[0].check_clause)

            # 8. Indexes (Partial index)
            indexes = await conn.list_indexes(schema=FIXTURE_SCHEMA, table="users")
            idx_names = [i.index_name for i in indexes]
            self.assertIn("idx_users_active_email", idx_names)
            active_idx = next(i for i in indexes if i.index_name == "idx_users_active_email")
            self.assertIsNotNone(active_idx.predicate)
            self.assertIn("active", active_idx.predicate or "")

            # 9. Views and Materialized Views
            views = await conn.list_views(schema=FIXTURE_SCHEMA)
            view_names = [v.view_name for v in views]
            self.assertIn("v_order_summary", view_names)
            self.assertIn("mv_active_user_stats", view_names)
            mv = next(v for v in views if v.view_name == "mv_active_user_stats")
            self.assertTrue(mv.is_materialized)

            # 10. Sequences
            sequences = await conn.list_sequences(schema=FIXTURE_SCHEMA)
            seq_names = [s.sequence_name for s in sequences]
            self.assertIn("order_seq", seq_names)
            order_seq = next(s for s in sequences if s.sequence_name == "order_seq")
            self.assertEqual(order_seq.start_value, 100)

            # 11. Partitions
            partitions = await conn.list_partitions(schema=FIXTURE_SCHEMA)
            part_tables = [p.table_name for p in partitions]
            self.assertIn("measurements", part_tables)

    async def test_live_read_only_transaction_enforcement(self) -> None:
        """Verify that read-only session rejects mutation attempts against live PostgreSQL."""
        async with self._get_test_connector() as conn:
            # Direct raw execute mutation on read-only session must fail with SQLSTATE 25006
            raw_conn = conn.connection_manager.raw_connection
            with self.assertRaises(Exception) as ctx:
                await raw_conn.execute(
                    f"INSERT INTO {FIXTURE_SCHEMA}.users (id, email) VALUES (999, 'hacked@example.com');"
                )
            self.assertIn("read-only transaction", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
