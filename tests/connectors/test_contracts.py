"""Unit Tests for DERA Connector Contracts and Metadata Schemas.

Validates:
- Engine identity and provider enums
- Capability registry, statuses, and discovery models
- Universal metadata models with deterministic field properties
- ConnectorConfig validation (network vs SQLite, secret masking)
"""

import unittest

from dera_connectors.capabilities import (
    CapabilityStatus,
    CapabilitySupport,
    ConnectorCapabilities,
    ConnectorCapability,
)
from dera_connectors.configuration import ConnectorConfig
from dera_connectors.engine import DatabaseEngine, DatabaseIdentity, DatabaseProvider
from dera_connectors.metadata import (
    CheckConstraintInfo,
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    PrimaryKeyInfo,
    SchemaInfo,
    TableInfo,
    UniqueConstraintInfo,
    ViewInfo,
)
from pydantic import SecretStr, ValidationError


class TestConnectorContracts(unittest.TestCase):
    """Test suite validating Phase 5.1 connector contracts and metadata representations."""

    def test_engine_identifiers(self) -> None:
        """Verify typed engine identifiers map to expected string dialects."""
        self.assertEqual(DatabaseEngine.POSTGRESQL.value, "postgresql")
        self.assertEqual(DatabaseEngine.SQLITE.value, "sqlite")
        self.assertEqual(DatabaseEngine.MYSQL.value, "mysql")
        self.assertEqual(DatabaseEngine.MARIADB.value, "mariadb")

    def test_database_identity_immutability(self) -> None:
        """Verify DatabaseIdentity model preserves sanitized attributes and is immutable."""
        identity = DatabaseIdentity(
            engine=DatabaseEngine.POSTGRESQL,
            server_version="16.2",
            driver_version="asyncpg-0.29.0",
            provider=DatabaseProvider.SUPABASE,
            database_name="customer_db",
        )
        self.assertEqual(identity.engine, DatabaseEngine.POSTGRESQL)
        self.assertEqual(identity.provider, DatabaseProvider.SUPABASE)
        self.assertEqual(identity.server_version, "16.2")

        with self.assertRaises(ValidationError):
            # Model is frozen
            identity.server_version = "17.0"  # type: ignore

    def test_capabilities_model_helpers(self) -> None:
        """Verify ConnectorCapabilities query methods (is_supported, get_status, filter lists)."""
        caps = ConnectorCapabilities(
            engine=DatabaseEngine.POSTGRESQL,
            capabilities={
                ConnectorCapability.TABLE_ENUMERATION: CapabilitySupport(
                    capability=ConnectorCapability.TABLE_ENUMERATION,
                    status=CapabilityStatus.SUPPORTED,
                ),
                ConnectorCapability.MATERIALIZED_VIEW_INSPECTION: CapabilitySupport(
                    capability=ConnectorCapability.MATERIALIZED_VIEW_INSPECTION,
                    status=CapabilityStatus.UNSUPPORTED,
                    reason="Not supported in this version",
                ),
                ConnectorCapability.FUNCTION_INSPECTION: CapabilitySupport(
                    capability=ConnectorCapability.FUNCTION_INSPECTION,
                    status=CapabilityStatus.RESTRICTED,
                    requires_permission="pg_read_all_settings",
                ),
            },
        )

        self.assertTrue(caps.is_supported(ConnectorCapability.TABLE_ENUMERATION))
        self.assertFalse(caps.is_supported(ConnectorCapability.MATERIALIZED_VIEW_INSPECTION))
        self.assertFalse(caps.is_supported(ConnectorCapability.FUNCTION_INSPECTION))
        self.assertFalse(caps.is_supported(ConnectorCapability.PROCEDURE_INSPECTION))

        self.assertEqual(
            caps.get_status(ConnectorCapability.TABLE_ENUMERATION), CapabilityStatus.SUPPORTED
        )
        self.assertEqual(
            caps.get_status(ConnectorCapability.MATERIALIZED_VIEW_INSPECTION),
            CapabilityStatus.UNSUPPORTED,
        )
        self.assertEqual(
            caps.get_status(ConnectorCapability.FUNCTION_INSPECTION), CapabilityStatus.RESTRICTED
        )
        self.assertEqual(
            caps.get_status(ConnectorCapability.PROCEDURE_INSPECTION), CapabilityStatus.UNKNOWN
        )

        self.assertEqual(caps.supported_capabilities(), [ConnectorCapability.TABLE_ENUMERATION])
        self.assertEqual(
            caps.unsupported_capabilities(), [ConnectorCapability.MATERIALIZED_VIEW_INSPECTION]
        )
        self.assertEqual(caps.restricted_capabilities(), [ConnectorCapability.FUNCTION_INSPECTION])

    def test_metadata_schema_models(self) -> None:
        """Verify TableInfo, ColumnInfo, constraints, and views instantiate with type integrity."""
        schema = SchemaInfo(schema_name="analytics", comment="Analytics schema")
        self.assertEqual(schema.schema_name, "analytics")

        table = TableInfo(schema_name="analytics", table_name="daily_metrics", object_type="TABLE")
        self.assertEqual(table.qualified_name, "analytics.daily_metrics")

        col = ColumnInfo(
            schema_name="analytics",
            table_name="daily_metrics",
            column_name="metric_value",
            ordinal_position=2,
            data_type="NUMERIC(10,2)",
            is_nullable=False,
            default_expression="0.00",
        )
        self.assertEqual(col.column_name, "metric_value")
        self.assertEqual(col.ordinal_position, 2)
        self.assertFalse(col.is_nullable)

        pk = PrimaryKeyInfo(
            schema_name="analytics",
            table_name="daily_metrics",
            column_names=["id"],
        )
        self.assertEqual(pk.column_names, ["id"])

        fk = ForeignKeyInfo(
            schema_name="analytics",
            table_name="daily_metrics",
            column_names=["metric_id"],
            referenced_schema="analytics",
            referenced_table="metric_definitions",
            referenced_columns=["id"],
            on_delete="CASCADE",
        )
        self.assertEqual(fk.on_delete, "CASCADE")

        uq = UniqueConstraintInfo(
            schema_name="analytics",
            table_name="daily_metrics",
            column_names=["day", "metric_id"],
        )
        self.assertEqual(len(uq.column_names), 2)

        ck = CheckConstraintInfo(
            schema_name="analytics",
            table_name="daily_metrics",
            check_clause="metric_value >= 0",
        )
        self.assertEqual(ck.check_clause, "metric_value >= 0")

        idx = IndexInfo(
            index_name="idx_daily_metrics_day",
            schema_name="analytics",
            table_name="daily_metrics",
            column_names=["day"],
            is_unique=False,
            index_type="BTREE",
        )
        self.assertEqual(idx.index_type, "BTREE")

        view = ViewInfo(
            schema_name="analytics",
            view_name="v_daily_summary",
            view_definition="SELECT day, SUM(metric_value) FROM daily_metrics GROUP BY day",
        )
        self.assertFalse(view.is_materialized)

    def test_configuration_validation_network_vs_sqlite(self) -> None:
        """Verify network configurations require host while SQLite forbids host and port."""
        # Valid network configuration
        pg_cfg = ConnectorConfig(
            engine=DatabaseEngine.POSTGRESQL,
            host="db.customer.internal",
            database="app_prod",
            username="analyst",
            password=SecretStr("super-secret-password-123"),
        )
        self.assertEqual(pg_cfg.port, 5432)  # Auto-defaulted
        self.assertEqual(pg_cfg.engine, DatabaseEngine.POSTGRESQL)

        # Network configuration missing host raises ValueError
        with self.assertRaises(ValueError):
            ConnectorConfig(
                engine=DatabaseEngine.POSTGRESQL,
                database="app_prod",
                username="analyst",
            )

        # Valid SQLite configuration
        sqlite_cfg = ConnectorConfig(
            engine=DatabaseEngine.SQLITE,
            database="/var/data/app.db",
        )
        self.assertIsNone(sqlite_cfg.host)
        self.assertIsNone(sqlite_cfg.port)

        # SQLite with host raises ValueError
        with self.assertRaises(ValueError):
            ConnectorConfig(
                engine=DatabaseEngine.SQLITE,
                host="localhost",
                database="/var/data/app.db",
            )

    def test_configuration_safe_dict_masks_secrets(self) -> None:
        """Verify password is never exposed in safe_dict, repr, or str."""
        raw_secret = "Confidential_Password_999!"
        cfg = ConnectorConfig(
            engine=DatabaseEngine.POSTGRESQL,
            host="postgres.internal.com",
            database="testdb",
            username="admin",
            password=SecretStr(raw_secret),
        )

        safe = cfg.safe_dict()
        self.assertNotIn(raw_secret, str(safe))
        self.assertNotIn("password", safe)
        self.assertTrue(safe["has_password"])

        # Check __repr__ and __str__
        self.assertNotIn(raw_secret, repr(cfg))
        self.assertNotIn(raw_secret, str(cfg))
