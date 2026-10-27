"""Tests for DERA Explicit Transaction Management.

Validates transaction_scope context manager, atomic commits, automatic rollbacks,
and preservation of database integrity upon error.
"""

import unittest

from dera_api.core.config import ApiSettings
from dera_api.db.base import Base
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.models.platform import PlatformMetadata
from dera_api.db.session import create_session_factory, transaction_scope
from sqlalchemy import select


class TestDatabaseTransactions(unittest.IsolatedAsyncioTestCase):
    """Test suite for explicit database transaction boundaries."""

    async def asyncSetUp(self) -> None:
        self.settings = ApiSettings(database_url="sqlite+aiosqlite:///:memory:")
        self.engine = create_database_engine(self.settings)
        # Create schema for transaction tests
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.session_factory = create_session_factory(self.engine)

    async def asyncTearDown(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await dispose_database_engine(self.engine)

    async def test_transaction_scope_atomic_commit(self) -> None:
        """Verify that operations within transaction_scope are atomically committed."""
        async with self.session_factory() as session:
            async with transaction_scope(session):
                item = PlatformMetadata(key="tx_test_key", value="tx_test_val")
                session.add(item)

        # Verify record exists in separate session
        async with self.session_factory() as verify_session:
            stmt = select(PlatformMetadata).where(PlatformMetadata.key == "tx_test_key")
            result = await verify_session.execute(stmt)
            persisted = result.scalar_one_or_none()
            self.assertIsNotNone(persisted)
            self.assertEqual(persisted.value, "tx_test_val")

    async def test_transaction_scope_rollback_on_exception(self) -> None:
        """Verify that an exception inside transaction_scope automatically rolls back."""
        with self.assertRaises(ValueError):
            async with self.session_factory() as session:
                async with transaction_scope(session):
                    item = PlatformMetadata(key="aborted_key", value="aborted_val")
                    session.add(item)
                    raise ValueError("Simulated business logic failure")

        # Verify aborted record does NOT exist
        async with self.session_factory() as verify_session:
            stmt = select(PlatformMetadata).where(PlatformMetadata.key == "aborted_key")
            result = await verify_session.execute(stmt)
            persisted = result.scalar_one_or_none()
            self.assertIsNone(persisted)

    async def test_nested_transaction_scope_savepoint(self) -> None:
        """Verify that nested transaction_scope uses savepoints correctly."""
        async with self.session_factory() as session:
            async with transaction_scope(session):
                item1 = PlatformMetadata(key="outer_key", value="outer_val")
                session.add(item1)

                try:
                    async with transaction_scope(session):
                        item2 = PlatformMetadata(key="inner_key", value="inner_val")
                        session.add(item2)
                        raise RuntimeError("Inner failure")
                except RuntimeError:
                    pass  # Inner savepoint rolled back

                item3 = PlatformMetadata(key="outer_key_2", value="outer_val_2")
                session.add(item3)

        async with self.session_factory() as verify_session:
            stmt1 = select(PlatformMetadata).where(PlatformMetadata.key == "outer_key")
            stmt2 = select(PlatformMetadata).where(PlatformMetadata.key == "inner_key")
            stmt3 = select(PlatformMetadata).where(PlatformMetadata.key == "outer_key_2")

            self.assertIsNotNone((await verify_session.execute(stmt1)).scalar_one_or_none())
            self.assertIsNone((await verify_session.execute(stmt2)).scalar_one_or_none())
            self.assertIsNotNone((await verify_session.execute(stmt3)).scalar_one_or_none())


if __name__ == "__main__":
    unittest.main()
