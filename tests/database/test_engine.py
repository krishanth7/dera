"""Tests for DERA Database Engine Factory, Configuration & Lifecycle.

Validates AsyncEngine creation, connection pool parameters, credential masking,
and clean engine disposal without import-time connection attempts.
"""

import unittest

from dera_api.core.config import ApiSettings
from dera_api.db.engine import create_database_engine, dispose_database_engine


class TestDatabaseEngine(unittest.IsolatedAsyncioTestCase):
    """Test suite for asynchronous database engine factory."""

    def test_unconfigured_database_url_raises_value_error(self) -> None:
        """Verify that attempting to create an engine without database_url raises ValueError."""
        settings = ApiSettings(database_url=None)
        with self.assertRaises(ValueError) as ctx:
            create_database_engine(settings)
        self.assertIn("Platform database URL is not configured", str(ctx.exception))

    async def test_sqlite_engine_creation_and_disposal(self) -> None:
        """Verify that SQLite async engine is created and disposed cleanly."""
        settings = ApiSettings(database_url="sqlite+aiosqlite:///:memory:")
        engine = create_database_engine(settings)
        self.assertIsNotNone(engine)
        self.assertEqual(engine.url.drivername, "sqlite+aiosqlite")

        # Test safe disposal
        await dispose_database_engine(engine)

    async def test_dispose_none_engine_is_safe(self) -> None:
        """Verify that dispose_database_engine(None) is a safe no-op."""
        await dispose_database_engine(None)

    def test_postgresql_engine_configuration(self) -> None:
        """Verify PostgreSQL engine pool parameters and settings without connecting."""
        settings = ApiSettings(
            database_url="postgresql+asyncpg://test_user:secret_pass@127.0.0.1:5432/test_db",
            db_pool_size=15,
            db_max_overflow=7,
            db_pool_timeout=25.0,
            db_pool_recycle=1200,
            db_connect_timeout=8.0,
            db_statement_timeout_ms=15000,
            db_ssl_mode="prefer",
        )
        engine = create_database_engine(settings)
        self.assertEqual(engine.url.drivername, "postgresql+asyncpg")
        self.assertEqual(engine.url.username, "test_user")
        self.assertEqual(engine.url.host, "127.0.0.1")
        self.assertEqual(engine.url.port, 5432)
        self.assertEqual(engine.url.database, "test_db")

    def test_sanitized_database_url_credential_masking(self) -> None:
        """Verify that settings.sanitized_database_url masks sensitive passwords."""
        settings = ApiSettings(
            database_url="postgresql+asyncpg://app_user:p@ssword123!@db.internal:5432/dera_prod",
        )
        sanitized = settings.sanitized_database_url
        self.assertNotIn("p@ssword123!", sanitized)
        self.assertIn(":***@", sanitized)
        self.assertIn("app_user", sanitized)
        self.assertIn("db.internal:5432/dera_prod", sanitized)


if __name__ == "__main__":
    unittest.main()
