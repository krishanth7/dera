"""Tests for Integration between Phase 5.1-5.4 Connectors and Phase 5.5 Normalizer."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

from dera.metadata.normalization import MetadataNormalizer
from dera.metadata.serialization import compute_canonical_database_hash
from dera_connectors.metadata import (
    ColumnInfo,
    DatabaseMetadataReport,
    ForeignKeyInfo,
    IndexInfo,
    PrimaryKeyInfo,
    SchemaInfo,
    TableInfo,
    TriggerInfo,
    ViewInfo,
)


class TestConnectorIntegration(unittest.TestCase):
    """Test suite integrating universal connector DatabaseMetadataReport with normalizer."""

    def test_universal_connector_report_normalization(self) -> None:
        """Verify normalization of a full DatabaseMetadataReport from Phase 5 connectors."""
        report = DatabaseMetadataReport(
            database_name="production_db",
            engine="postgresql",
            server_version="16.2",
            schemas=[
                SchemaInfo(schema_name="public", comment="Primary schema"),
                SchemaInfo(schema_name="analytics", comment="Analytics reporting"),
            ],
            tables=[
                TableInfo(schema_name="public", table_name="customers"),
                TableInfo(schema_name="public", table_name="orders"),
            ],
            columns=[
                ColumnInfo(
                    schema_name="public",
                    table_name="customers",
                    column_name="id",
                    ordinal_position=1,
                    data_type="bigint",
                    is_nullable=False,
                ),
                ColumnInfo(
                    schema_name="public",
                    table_name="customers",
                    column_name="name",
                    ordinal_position=2,
                    data_type="text",
                    is_nullable=False,
                ),
                ColumnInfo(
                    schema_name="public",
                    table_name="orders",
                    column_name="id",
                    ordinal_position=1,
                    data_type="bigint",
                    is_nullable=False,
                ),
                ColumnInfo(
                    schema_name="public",
                    table_name="orders",
                    column_name="customer_id",
                    ordinal_position=2,
                    data_type="bigint",
                    is_nullable=False,
                ),
                ColumnInfo(
                    schema_name="public",
                    table_name="orders",
                    column_name="amount",
                    ordinal_position=3,
                    data_type="numeric(10,2)",
                    is_nullable=False,
                ),
            ],
            primary_keys=[
                PrimaryKeyInfo(
                    schema_name="public",
                    table_name="customers",
                    constraint_name="pk_customers",
                    column_names=["id"],
                ),
                PrimaryKeyInfo(
                    schema_name="public",
                    table_name="orders",
                    constraint_name="pk_orders",
                    column_names=["id"],
                ),
            ],
            foreign_keys=[
                ForeignKeyInfo(
                    schema_name="public",
                    table_name="orders",
                    constraint_name="fk_orders_customer",
                    column_names=["customer_id"],
                    referenced_table="customers",
                    referenced_schema="public",
                    referenced_columns=["id"],
                    on_delete="CASCADE",
                )
            ],
            unique_constraints=[],
            check_constraints=[],
            indexes=[
                IndexInfo(
                    schema_name="public",
                    table_name="orders",
                    index_name="idx_orders_customer",
                    column_names=["customer_id"],
                )
            ],
            views=[
                ViewInfo(
                    schema_name="analytics",
                    view_name="v_daily_sales",
                    view_definition="SELECT customer_id, sum(amount) FROM orders GROUP BY 1",
                )
            ],
            triggers=[
                TriggerInfo(
                    schema_name="public",
                    table_name="orders",
                    trigger_name="tr_orders_audit",
                    timing="AFTER",
                    event="INSERT",
                )
            ],
            inspected_at=datetime.now(UTC),
        )

        normalizer = MetadataNormalizer(
            engine="postgresql",
            database_name="production_db",
            server_version="16.2",
            workspace_id="ws_retail",
            connection_id="conn_primary",
        )

        canonical_db = normalizer.normalize(report)

        # Assertions
        self.assertEqual(canonical_db.engine, "postgresql")
        self.assertEqual(len(canonical_db.namespaces), 2)
        pub_ns = canonical_db.get_namespace("public")
        self.assertIsNotNone(pub_ns)
        self.assertEqual(len(pub_ns.tables), 2)

        # Check FK referential link
        orders_tbl = pub_ns.get_table("orders")
        self.assertIsNotNone(orders_tbl)
        self.assertEqual(len(orders_tbl.foreign_keys), 1)
        fk = orders_tbl.foreign_keys[0]
        self.assertEqual(fk.name, "fk_orders_customer")
        self.assertEqual(fk.referenced_table_name, "customers")

        # Check Triggers
        self.assertEqual(len(orders_tbl.triggers), 1)
        self.assertEqual(orders_tbl.triggers[0].name, "tr_orders_audit")

        # Check deterministic hash
        db_hash = compute_canonical_database_hash(canonical_db)
        self.assertEqual(len(db_hash), 64)


if __name__ == "__main__":
    unittest.main()
