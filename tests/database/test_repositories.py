"""Tests for DERA Database Repositories.

Validates PlatformMetadataRepository CRUD operations, update behaviors,
ordered listing, and key-based deletions using async session.
"""

import unittest

from dera_api.core.config import ApiSettings
from dera_api.db.base import Base
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.session import create_session_factory
from dera_api.repositories.base import PlatformMetadataRepository


class TestPlatformMetadataRepository(unittest.IsolatedAsyncioTestCase):
    """Test suite for PlatformMetadataRepository operations."""

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

    async def test_set_and_get_metadata(self) -> None:
        """Verify creating and retrieving metadata by key."""
        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            created = await repo.set_value(
                key="schema_baseline_version",
                value="1.0.0",
                description="Authoritative initial schema baseline",
            )
            await session.commit()
            self.assertEqual(created.key, "schema_baseline_version")
            self.assertEqual(created.value, "1.0.0")

        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            fetched = await repo.get_by_key("schema_baseline_version")
            self.assertIsNotNone(fetched)
            assert fetched is not None
            self.assertEqual(fetched.value, "1.0.0")
            self.assertEqual(fetched.description, "Authoritative initial schema baseline")

    async def test_set_value_updates_existing_record(self) -> None:
        """Verify that calling set_value on existing key updates value in-place."""
        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            await repo.set_value(key="feature_flag_x", value="disabled")
            await session.commit()

        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            updated = await repo.set_value(key="feature_flag_x", value="enabled")
            await session.commit()
            self.assertEqual(updated.value, "enabled")

        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            fetched = await repo.get_by_key("feature_flag_x")
            self.assertIsNotNone(fetched)
            assert fetched is not None
            self.assertEqual(fetched.value, "enabled")

    async def test_get_by_key_not_found(self) -> None:
        """Verify that get_by_key returns None for missing key."""
        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            result = await repo.get_by_key("non_existent_key")
            self.assertIsNone(result)

    async def test_list_all(self) -> None:
        """Verify that list_all returns all records ordered by key."""
        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            await repo.set_value(key="key_b", value="val_b")
            await repo.set_value(key="key_a", value="val_a")
            await session.commit()

        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            all_records = await repo.list_all()
            self.assertEqual(len(all_records), 2)
            self.assertEqual(all_records[0].key, "key_a")
            self.assertEqual(all_records[1].key, "key_b")

    async def test_delete_by_key(self) -> None:
        """Verify deleting record by key returns True when found and False when missing."""
        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            await repo.set_value(key="to_delete", value="temp")
            await session.commit()

        async with self.session_factory() as session:
            repo = PlatformMetadataRepository(session)
            deleted = await repo.delete_by_key("to_delete")
            await session.commit()
            self.assertTrue(deleted)

            # Deleting again should return False
            deleted_again = await repo.delete_by_key("to_delete")
            self.assertFalse(deleted_again)


if __name__ == "__main__":
    unittest.main()
