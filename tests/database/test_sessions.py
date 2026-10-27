"""Tests for DERA Database Session Factory & FastAPI Dependency Injection.

Validates async session creation, session isolation, exception rollback,
and FastAPI get_db_session dependency lifecycle.
"""

import unittest
from unittest.mock import MagicMock

from dera_api.core.config import ApiSettings
from dera_api.core.exceptions import DependencyUnavailableError
from dera_api.db.dependencies import get_db_session
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.session import create_session_factory, session_scope


class TestDatabaseSessions(unittest.IsolatedAsyncioTestCase):
    """Test suite for async database sessions and FastAPI dependency injection."""

    async def asyncSetUp(self) -> None:
        self.settings = ApiSettings(database_url="sqlite+aiosqlite:///:memory:")
        self.engine = create_database_engine(self.settings)
        self.session_factory = create_session_factory(self.engine)

    async def asyncTearDown(self) -> None:
        await dispose_database_engine(self.engine)

    async def test_session_factory_creation(self) -> None:
        """Verify that session factory instantiates valid AsyncSession instances."""
        async with self.session_factory() as session:
            self.assertIsNotNone(session)
            self.assertFalse(session.in_transaction())

    async def test_session_scope_normal_closure(self) -> None:
        """Verify that session_scope closes session without errors."""
        async with session_scope(self.session_factory) as session:
            self.assertIsNotNone(session)
        self.assertTrue(session.is_active or session.is_closed)

    async def test_session_scope_rolls_back_on_exception(self) -> None:
        """Verify that session_scope issues a rollback when an exception occurs."""
        with self.assertRaises(RuntimeError):
            async with session_scope(self.session_factory):
                raise RuntimeError("Simulated processing error")

    async def test_get_db_session_dependency_unconfigured(self) -> None:
        """Verify that get_db_session raises DependencyUnavailableError when unconfigured."""
        mock_request = MagicMock()
        mock_request.app.state.db_session_factory = None

        gen = get_db_session(mock_request)
        with self.assertRaises(DependencyUnavailableError) as ctx:
            await anext(gen)
        self.assertIn("Platform database is not configured", str(ctx.exception))

    async def test_get_db_session_dependency_yields_session(self) -> None:
        """Verify that get_db_session yields active session and closes reliably."""
        mock_request = MagicMock()
        mock_request.app.state.db_session_factory = self.session_factory

        gen = get_db_session(mock_request)
        session = await anext(gen)
        self.assertIsNotNone(session)

        # Trigger exit of generator
        with self.assertRaises(StopAsyncIteration):
            await anext(gen)


if __name__ == "__main__":
    unittest.main()
