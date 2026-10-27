"""Tests for Supabase PostgreSQL connection compatibility, pooler modes, and TLS."""

import unittest

from dera_connectors.capabilities import CapabilityStatus, ConnectorCapability
from dera_connectors.engine import DatabaseEngine, DatabaseProvider
from dera_connectors.postgresql.capabilities import get_postgres_capabilities
from dera_connectors.postgresql.configuration import (
    PostgresConnectorConfig,
    SupabasePoolerMode,
)
from pydantic import SecretStr


class TestSupabaseCompatibility(unittest.TestCase):
    """Verify Supabase PostgreSQL connection modes and PgBouncer safety."""

    def test_direct_connection_mode(self) -> None:
        """Verify Supabase direct connection configuration defaults to port 5432."""
        config = PostgresConnectorConfig(
            database="postgres",
            host="db.abcdefghijkl.supabase.co",
            username="postgres",
            password=SecretStr("supersecret"),
            supabase_pooler_mode=SupabasePoolerMode.DIRECT,
        )
        self.assertEqual(config.provider, DatabaseProvider.SUPABASE)
        self.assertEqual(config.port, 5432)
        self.assertGreater(config.statement_cache_size, 0)

    def test_session_pooler_mode(self) -> None:
        """Verify Supabase session pooler connection defaults to port 6543."""
        config = PostgresConnectorConfig(
            database="postgres",
            host="aws-0-us-west-1.pooler.supabase.com",
            username="postgres.abcdefghijkl",
            password=SecretStr("supersecret"),
            supabase_pooler_mode=SupabasePoolerMode.SESSION,
        )
        self.assertEqual(config.provider, DatabaseProvider.SUPABASE)
        self.assertEqual(config.port, 6543)
        self.assertGreater(config.statement_cache_size, 0)

    def test_transaction_pooler_disables_prepared_statements(self) -> None:
        """Verify Supabase transaction pooler (PgBouncer) forces statement_cache_size=0."""
        config = PostgresConnectorConfig(
            database="postgres",
            host="aws-0-us-west-1.pooler.supabase.com",
            username="postgres.abcdefghijkl",
            password=SecretStr("supersecret"),
            supabase_pooler_mode=SupabasePoolerMode.TRANSACTION,
        )
        self.assertEqual(config.provider, DatabaseProvider.SUPABASE)
        self.assertEqual(config.port, 6543)
        self.assertEqual(config.statement_cache_size, 0)

        kwargs = config.build_asyncpg_kwargs()
        self.assertEqual(kwargs["statement_cache_size"], 0)

    def test_supabase_capabilities(self) -> None:
        """Verify capability matrix reports full metadata inspection support for Supabase."""
        caps = get_postgres_capabilities(provider=DatabaseProvider.SUPABASE)
        self.assertEqual(caps.engine, DatabaseEngine.POSTGRESQL)
        self.assertEqual(
            caps.capabilities[ConnectorCapability.TABLE_ENUMERATION].status,
            CapabilityStatus.SUPPORTED,
        )
        self.assertEqual(
            caps.capabilities[ConnectorCapability.VIEW_INSPECTION].status,
            CapabilityStatus.SUPPORTED,
        )
        self.assertTrue(caps.is_supported(ConnectorCapability.TABLE_ENUMERATION))
        self.assertTrue(caps.is_supported(ConnectorCapability.VIEW_INSPECTION))


if __name__ == "__main__":
    unittest.main()
