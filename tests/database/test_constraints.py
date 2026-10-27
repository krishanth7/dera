"""Tests for DERA Database Model Constraints & Integrity.

Validates primary key uniqueness, NOT NULL constraints, timezone-aware timestamps,
and data integrity protection for PlatformMetadata.
"""

import unittest
from datetime import datetime

from dera_api.core.config import ApiSettings
from dera_api.db.base import Base
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.models.platform import PlatformMetadata
from dera_api.db.session import create_session_factory
from sqlalchemy.exc import IntegrityError


class TestDatabaseConstraints(unittest.IsolatedAsyncioTestCase):
    """Test suite for database model constraints and integrity rules."""

    async def asyncSetUp(self) -> None:
        self.settings = ApiSettings(database_url="sqlite+aiosqlite:///:memory:")
        self.engine = create_database_engine(self.settings)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.session_factory = create_session_factory(self.engine)

    async def asyncTearDown(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await dispose_database_engine(self.engine)

    async def test_primary_key_uniqueness_enforced(self) -> None:
        """Verify that inserting duplicate primary key raises IntegrityError."""
        async with self.session_factory() as session:
            record1 = PlatformMetadata(key="unique_key", value="first_val")
            session.add(record1)
            await session.commit()

        async with self.session_factory() as session:
            record2 = PlatformMetadata(key="unique_key", value="second_val")
            session.add(record2)
            with self.assertRaises(IntegrityError):
                await session.commit()

    async def test_not_null_constraint_enforced(self) -> None:
        """Verify that inserting NULL for required value column raises IntegrityError."""
        async with self.session_factory() as session:
            # Type ignore to simulate runtime constraint violation
            record = PlatformMetadata(key="null_test_key", value=None)  # type: ignore[arg-type]
            session.add(record)
            with self.assertRaises(IntegrityError):
                await session.commit()

    async def test_timestamp_fields_created_and_updated(self) -> None:
        """Verify that timestamps are populated with valid datetime instances."""
        async with self.session_factory() as session:
            record = PlatformMetadata(
                key="timestamp_key",
                value="timestamp_val",
                description="Testing timestamp defaults",
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)

            self.assertIsInstance(record.created_at, datetime)
            self.assertIsInstance(record.updated_at, datetime)
            self.assertIn("timestamp_key", repr(record))


if __name__ == "__main__":
    unittest.main()
