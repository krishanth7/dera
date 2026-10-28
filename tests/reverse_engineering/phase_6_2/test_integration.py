"""End-to-End Integration tests connecting Real SQLite Database -> Connector -> Metadata -> Schema -> Structural Reconstruction."""

import os
import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime

from dera.metadata.normalization import MetadataNormalizer
from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.reconstruction.builder import StructuralReconstructionBuilder
from dera_connectors.context import ConnectorContext
from dera_connectors.metadata import DatabaseMetadataReport
from dera_connectors.sqlite.adapter import SqliteConnector
from dera_connectors.sqlite.configuration import SqliteConnectorConfig


class TestRealDatabaseStructuralReconstruction(unittest.IsolatedAsyncioTestCase):
    """End-to-end integration test with a real disposable SQLite database."""

    async def asyncSetUp(self) -> None:
        """Create disposable SQLite database with relational tables, foreign keys, and constraints."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "real_structural_integration.db")

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
            """
        )
        conn.commit()
        conn.close()

    async def asyncTearDown(self) -> None:
        """Clean up disposable test directory."""
        self.temp_dir.cleanup()

    async def test_full_pipeline_to_structural_reconstruction(self) -> None:
        """Test full pipeline: SQLite DB -> SqliteConnector -> MetadataNormalizer -> SchemaBuilder -> StructuralReconstructionBuilder."""
        config = SqliteConnectorConfig(
            database=self.db_path,
            read_only=True,
        )
        context = ConnectorContext(workspace_id="ws_structural_integration")

        # 1. Real Connector extraction
        async with SqliteConnector(config, context=context) as connector:
            schemas = await connector.list_schemas()
            tables = await connector.list_tables()
            all_columns = []
            all_pks = []
            all_fks = []
            all_unqs = []
            all_chks = []

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

            report = DatabaseMetadataReport(
                database_name="main",
                engine="sqlite",
                engine_version="3.45.0",
                extracted_at=datetime.now(UTC),
                schemas=schemas,
                tables=tables,
                columns=all_columns,
                primary_keys=all_pks,
                foreign_keys=all_fks,
                unique_constraints=all_unqs,
                check_constraints=all_chks,
                indexes=[],
                views=[],
                triggers=[],
            )

        # 2. Phase 5.5 Canonical Normalization
        normalizer = MetadataNormalizer(
            engine="sqlite",
            database_name="main",
            workspace_id="ws_structural_integration",
        )
        canonical_db = normalizer.normalize(report)
        self.assertEqual(canonical_db.engine, "sqlite")

        # 3. Phase 6.1 Schema Representation
        schema_rep = SchemaBuilder.from_canonical_database(canonical_db)
        self.assertEqual(len(schema_rep.tables), 2)

        # 4. Phase 6.2 Structural Reconstruction
        recon_builder = StructuralReconstructionBuilder()
        result = recon_builder.build(schema_rep)

        # 5. Assertions on reconstructed models
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.tables), 2)

        cust_table = result.get_table_by_name("main", "customers")
        self.assertIsNotNone(cust_table)
        assert cust_table is not None
        self.assertEqual(len(cust_table.columns), 4)
        self.assertIsNotNone(cust_table.primary_key)
        self.assertEqual(cust_table.primary_key.column_names, ("customer_id",))
        self.assertEqual(len(cust_table.unique_constraints), 1)
        self.assertEqual(cust_table.unique_constraints[0].column_names, ("contact_email",))

        orders_table = result.get_table_by_name("main", "orders")
        self.assertIsNotNone(orders_table)
        assert orders_table is not None
        self.assertEqual(len(orders_table.foreign_keys), 1)
        fk = orders_table.foreign_keys[0]
        self.assertEqual(fk.source_column_names, ("customer_id",))
        self.assertEqual(fk.referenced_table_name, "customers")
        self.assertEqual(fk.referenced_column_names, ("customer_id",))
        self.assertEqual(fk.resolution_status.value, "resolved")
        self.assertEqual(fk.referenced_table_id, cust_table.object_id)


if __name__ == "__main__":
    unittest.main()
