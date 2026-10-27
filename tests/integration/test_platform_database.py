"""Integration Tests for DERA Platform Database (PostgreSQL & Async Engine).

Validates end-to-end database connectivity, schema creation, repository persistence,
and explicit transaction isolation against PostgreSQL service (in CI/local Docker)
or async database engine.
"""

import os
import unittest

from dera_api.core.config import ApiSettings
from dera_api.db.base import Base
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.health import check_database_health
from dera_api.db.session import create_session_factory, transaction_scope
from dera_api.repositories.base import PlatformMetadataRepository
from sqlalchemy import text


class TestPlatformDatabaseIntegration(unittest.IsolatedAsyncioTestCase):
    """Authoritative integration tests for DERA platform database."""

    async def asyncSetUp(self) -> None:
        # Determine database target from environment (e.g. GitHub Actions PostgreSQL service)
        db_url = os.getenv(
            "DERA_PLATFORM_DATABASE_URL",
            "sqlite+aiosqlite:///:memory:",
        )
        self.settings = ApiSettings(
            database_url=db_url,
            db_pool_size=5,
            db_max_overflow=2,
            db_statement_timeout_ms=10000,
        )
        self.engine = create_database_engine(self.settings)

        # Check if engine can connect
        is_healthy = await check_database_health(self.engine, timeout_seconds=3.0)
        if not is_healthy and "postgresql" in db_url:
            self.skipTest(
                f"Live PostgreSQL instance not reachable at {self.settings.sanitized_database_url}"
            )

        # Set up schema
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.session_factory = create_session_factory(self.engine)

    async def asyncTearDown(self) -> None:
        if hasattr(self, "engine"):
            if "sqlite" in str(self.engine.url):
                try:
                    async with self.engine.begin() as conn:
                        await conn.run_sync(Base.metadata.drop_all)
                except Exception:
                    pass
            else:
                try:
                    async with self.engine.begin() as conn:
                        await conn.execute(
                            text(
                                "DELETE FROM dera_platform_metadata WHERE key LIKE 'integration_test_%'"
                            )
                        )
                except Exception:
                    pass
            await dispose_database_engine(self.engine)

    async def test_database_health_check(self) -> None:
        """Verify that check_database_health executes SELECT 1; successfully."""
        healthy = await check_database_health(self.engine)
        self.assertTrue(healthy)

    async def test_full_repository_lifecycle_in_transaction(self) -> None:
        """Verify creating, querying, updating, and deleting metadata in explicit transactions."""
        async with self.session_factory() as session:
            async with transaction_scope(session):
                repo = PlatformMetadataRepository(session)
                record = await repo.set_value(
                    key="integration_test_key",
                    value="platform_v1_payload",
                    description="Integration test metadata record",
                )
                self.assertEqual(record.key, "integration_test_key")

        # Verify in a second independent session
        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            persisted = await repo.get_by_key("integration_test_key")
            self.assertIsNotNone(persisted)
            assert persisted is not None
            self.assertEqual(persisted.value, "platform_v1_payload")

            # Update record
            async with transaction_scope(session):
                await repo.set_value(
                    key="integration_test_key",
                    value="platform_v1_updated",
                )

        # Verify update and then delete
        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            updated = await repo.get_by_key("integration_test_key")
            self.assertIsNotNone(updated)
            assert updated is not None
            self.assertEqual(updated.value, "platform_v1_updated")

            async with transaction_scope(session):
                deleted = await repo.delete_by_key("integration_test_key")
                self.assertTrue(deleted)

        # Verify deletion
        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            deleted_check = await repo.get_by_key("integration_test_key")
            self.assertIsNone(deleted_check)

    async def test_direct_sql_bounded_execution(self) -> None:
        """Verify executing lightweight SQL commands with bound parameters."""
        sql_stmt = text("SELECT CAST(:num AS INTEGER) AS answer")

        async with self.engine.connect() as conn:
            result = await conn.execute(sql_stmt, {"num": 42})
            row = result.fetchone()
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row[0], 42)


if __name__ == "__main__":
    unittest.main()
