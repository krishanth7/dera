"""End-to-End Integration tests connecting Real SQLite Database -> Connector -> Metadata -> Schema Representation."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from dera.metadata.normalization import MetadataNormalizer
from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.schema import SchemaRepresentation
from dera.reverse_engineering.serialization import serialize_schema_representation
from dera_connectors.context import ConnectorContext
from dera_connectors.sqlite.adapter import SqliteConnector
from dera_connectors.sqlite.configuration import SqliteConnectorConfig


class TestRealDatabaseIntegration(unittest.IsolatedAsyncioTestCase):
    """End-to-end integration test with a real disposable SQLite database."""

    async def asyncSetUp(self) -> None:
        """Create disposable SQLite database with relational tables, foreign keys, indexes, and triggers."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "real_integration.db")

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                contact_email TEXT UNIQUE NOT NULL,
                credit_limit REAL DEFAULT 5000.0
            );

            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                order_status TEXT CHECK (order_status IN ('DRAFT', 'CONFIRMED', 'SHIPPED')),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON UPDATE CASCADE ON DELETE RESTRICT
            );

            CREATE INDEX idx_orders_customer ON orders(customer_id);

            CREATE VIEW v_active_orders AS
                SELECT o.order_id, c.company_name, o.total_amount
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id;

            CREATE TRIGGER trg_orders_audit
            AFTER INSERT ON orders
            BEGIN
                SELECT 1;
            END;
            """
        )
        conn.commit()
        conn.close()

    async def asyncTearDown(self) -> None:
        """Clean up disposable test directory."""
        self.temp_dir.cleanup()

    async def test_full_pipeline_real_database_to_validated_schema(self) -> None:
        """Test full pipeline: Disposable SQLite DB -> SqliteConnector -> MetadataNormalizer -> SchemaBuilder -> SchemaRepresentation."""
        config = SqliteConnectorConfig(
            database=self.db_path,
            read_only=True,
        )
        context = ConnectorContext(workspace_id="ws_integration")

        from datetime import UTC, datetime

        from dera_connectors.metadata import DatabaseMetadataReport

        # 1. Real Connector inspection
        async with SqliteConnector(config, context=context) as connector:
            schemas = await connector.list_schemas()
            tables = await connector.list_tables()
            all_columns = []
            all_pks = []
            all_fks = []
            all_unqs = []
            all_chks = []
            all_indexes = []
            all_triggers = []

            for tbl in tables:
                cols = await connector.list_columns(tbl.schema_name, tbl.table_name)
                all_columns.extend(cols)
                pk = await connector.get_primary_key(tbl.schema_name, tbl.table_name)
                if pk:
                    all_pks.append(pk)
                fks = await connector.list_foreign_keys(tbl.schema_name, tbl.table_name)
                all_fks.extend(fks)
                unqs = await connector.list_unique_constraints(tbl.schema_name, tbl.table_name)
                all_unqs.extend(unqs)
                chks = await connector.list_check_constraints(tbl.schema_name, tbl.table_name)
                all_chks.extend(chks)
                idxs = await connector.list_indexes(tbl.schema_name, tbl.table_name)
                all_indexes.extend(idxs)
                trgs = await connector.list_triggers(tbl.schema_name, tbl.table_name)
                all_triggers.extend(trgs)

            views = await connector.list_views()

            report = DatabaseMetadataReport(
                database_name="main",
                engine="sqlite",
                server_version="3.45.0",
                schemas=schemas,
                tables=tables,
                columns=all_columns,
                primary_keys=all_pks,
                foreign_keys=all_fks,
                unique_constraints=all_unqs,
                check_constraints=all_chks,
                indexes=all_indexes,
                views=views,
                triggers=all_triggers,
                inspected_at=datetime.now(UTC),
            )

        # 2. Canonical Normalization
        normalizer = MetadataNormalizer(
            engine="sqlite",
            database_name="main",
            workspace_id="ws_integration",
        )
        canonical_db = normalizer.normalize(report)
        self.assertEqual(canonical_db.engine, "sqlite")

        # 3. Phase 6.1 Schema Construction
        schema = SchemaBuilder.from_canonical_database(
            canonical_db,
            workspace_id="ws_integration",
            strict_validation=True,
        )

        self.assertIsInstance(schema, SchemaRepresentation)
        self.assertEqual(schema.engine, "sqlite")
        self.assertTrue(schema.is_validated)
        self.assertEqual(len(schema.validation_issues), 0)

        # 4. Verify Object Registry contains all inspected objects
        cust_tbl = schema.find_table("main", "customers")
        self.assertIsNotNone(cust_tbl)
        self.assertTrue(schema.contains(cust_tbl.id))

        orders_tbl = schema.find_table("main", "orders")
        self.assertIsNotNone(orders_tbl)
        self.assertTrue(schema.contains(orders_tbl.id))

        # 5. Verify Foreign Key Resolution
        fk_refs = schema.foreign_key_references
        self.assertEqual(len(fk_refs), 1)
        fk = fk_refs[0]
        self.assertEqual(fk.source_table_name, "orders")
        self.assertEqual(fk.referenced_table_name, "customers")
        self.assertTrue(fk.is_resolved)
        self.assertEqual(fk.referenced_table_id, cust_tbl.id)

        # 6. Verify Hierarchical Navigation
        tables = schema.hierarchy.tables(cust_tbl.namespace_id)
        self.assertEqual(len(tables), 2)
        table_names = [t.name for t in tables]
        self.assertEqual(table_names, ["customers", "orders"])

        # 7. Verify Deterministic Serialization
        json_out = serialize_schema_representation(schema)
        self.assertIn('"customers"', json_out)
        self.assertIn('"orders"', json_out)
        self.assertIn('"v_active_orders"', json_out)
        self.assertIsNotNone(schema.compute_hash())


if __name__ == "__main__":
    unittest.main()
