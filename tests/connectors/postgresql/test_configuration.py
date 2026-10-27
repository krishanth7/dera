"""Tests for PostgresConnectorConfig and Supabase configuration models."""

import unittest

from dera_connectors.configuration import TimeoutSettings
from dera_connectors.engine import DatabaseEngine, DatabaseProvider
from dera_connectors.postgresql.configuration import (
    PostgresConnectorConfig,
    SupabasePoolerMode,
)
from pydantic import SecretStr


class TestPostgresConfiguration(unittest.TestCase):
    """Verify configuration validation, defaults, and Supabase detection."""

    def test_default_postgres_configuration(self) -> None:
        """Verify standard PostgreSQL default parameters."""
        config = PostgresConnectorConfig(
            database="test_db",
            host="postgres.internal",
            username="analyst",
            password=SecretStr("supersecret"),
        )
        self.assertEqual(config.engine, DatabaseEngine.POSTGRESQL)
        self.assertEqual(config.provider, DatabaseProvider.GENERIC)
        self.assertEqual(config.port, 5432)
        self.assertEqual(config.application_name, "DERA_Connector_v5.2")
        self.assertEqual(config.statement_timeout_ms, 30000)
        self.assertEqual(config.statement_cache_size, 100)
        self.assertEqual(config.supabase_pooler_mode, SupabasePoolerMode.DIRECT)

    def test_supabase_host_auto_detection(self) -> None:
        """Verify automatic detection of Supabase provider from host domain."""
        config = PostgresConnectorConfig(
            database="postgres",
            host="db.abcdefghijkl.supabase.co",
            username="postgres",
        )
        self.assertEqual(config.provider, DatabaseProvider.SUPABASE)

        config_pooler = PostgresConnectorConfig(
            database="postgres",
            host="aws-0-us-east-1.pooler.supabase.com",
            username="postgres.abcdefghijkl",
            supabase_pooler_mode=SupabasePoolerMode.TRANSACTION,
        )
        self.assertEqual(config_pooler.provider, DatabaseProvider.SUPABASE)
        self.assertEqual(config_pooler.port, 6543)
        # Transaction mode pooler disables prepared statement cache
        self.assertEqual(config_pooler.statement_cache_size, 0)

    def test_supabase_session_pooler_port_default(self) -> None:
        """Verify port defaults to 6543 for session pooler mode if unspecified."""
        config = PostgresConnectorConfig(
            database="postgres",
            host="my-host.com",
            supabase_pooler_mode=SupabasePoolerMode.SESSION,
        )
        self.assertEqual(config.port, 6543)

    def test_build_asyncpg_kwargs(self) -> None:
        """Verify asyncpg connection arguments construction."""
        config = PostgresConnectorConfig(
            database="analytics",
            host="10.0.0.5",
            port=5432,
            username="readonly_user",
            password=SecretStr("safe_pw"),
            timeouts=TimeoutSettings(connect_timeout_seconds=5.0, query_timeout_seconds=15.0),
        )
        kwargs = config.build_asyncpg_kwargs()
        self.assertEqual(kwargs["database"], "analytics")
        self.assertEqual(kwargs["host"], "10.0.0.5")
        self.assertEqual(kwargs["port"], 5432)
        self.assertEqual(kwargs["user"], "readonly_user")
        self.assertEqual(kwargs["password"], "safe_pw")
        self.assertEqual(kwargs["timeout"], 5.0)
        self.assertEqual(kwargs["command_timeout"], 15.0)
        self.assertEqual(kwargs["server_settings"]["application_name"], "DERA_Connector_v5.2")
        self.assertEqual(kwargs["server_settings"]["statement_timeout"], "30000")


if __name__ == "__main__":
    unittest.main()
