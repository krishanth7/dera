"""Tests for Database Health & Readiness Probe Integration.

Validates the bounded SELECT 1; connectivity probe, timeout handling,
and readiness check behavior with and without configured platform database.
"""

import unittest

from dera_api.core.config import ApiSettings
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.health import check_database_health
from dera_api.factory import create_app
from httpx import ASGITransport, AsyncClient


class TestDatabaseHealth(unittest.IsolatedAsyncioTestCase):
    """Test suite for database health and readiness probe verification."""

    async def asyncSetUp(self) -> None:
        self.settings = ApiSettings(database_url="sqlite+aiosqlite:///:memory:")
        self.engine = create_database_engine(self.settings)

    async def asyncTearDown(self) -> None:
        await dispose_database_engine(self.engine)

    async def test_check_database_health_success(self) -> None:
        """Verify that check_database_health returns True on active engine."""
        healthy = await check_database_health(self.engine, timeout_seconds=3.0)
        self.assertTrue(healthy)

    async def test_check_database_health_none_engine(self) -> None:
        """Verify that check_database_health returns False when engine is None."""
        healthy = await check_database_health(None)
        self.assertFalse(healthy)

    async def test_check_database_health_disposed_engine(self) -> None:
        """Verify that check_database_health handles closed engines safely."""
        test_engine = create_database_engine(self.settings)
        await dispose_database_engine(test_engine)
        healthy = await check_database_health(test_engine, timeout_seconds=1.0)
        # SQLite after dispose may reconnect or fail gracefully, but must never crash
        self.assertIsInstance(healthy, bool)

    async def test_readiness_probe_with_healthy_database(self) -> None:
        """Verify that /health/ready reports platform_database as operational when engine is configured."""
        app = create_app(self.settings)
        app.state.is_ready = True
        app.state.db_engine = self.engine

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/health/ready")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["ready"])
            self.assertEqual(data["subsystems"]["platform_database"], "operational")

    async def test_readiness_probe_without_database(self) -> None:
        """Verify that /health/ready reports platform_database as not_configured in stateless mode."""
        app = create_app(self.settings)
        app.state.is_ready = True
        app.state.db_engine = None

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/health/ready")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["ready"])
            self.assertEqual(data["subsystems"]["platform_database"], "not_configured")


if __name__ == "__main__":
    unittest.main()
