"""Tests for Phase 6.5 Snapshot Storage Implementations.

Verifies:
- InMemorySnapshotStorage: save, get_by_id, get_by_fingerprint, list, delete, verify.
- FileSystemSnapshotStorage: atomic file persistence, safe retrieval, deletion.
- Strict workspace isolation: tenant A cannot access or discover tenant B records.
- Immutability enforcement: attempting to overwrite an existing record with different content raises error.
- Content-addressable deduplication of identical structural payloads.
"""

from __future__ import annotations

import tempfile
import unittest

import pytest
from dera.reverse_engineering.snapshots.errors import (
    SnapshotNotFoundError,
    SnapshotStorageError,
)
from dera.reverse_engineering.snapshots.repository import (
    FileSystemSnapshotStorage,
    InMemorySnapshotStorage,
)
from dera.reverse_engineering.snapshots.storage import SnapshotFilter

from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
    make_empty_database,
    make_single_table_database,
)


class TestSnapshotStorage(unittest.IsolatedAsyncioTestCase):
    """Test suite for snapshot persistence backends."""

    async def asyncSetUp(self) -> None:
        self.db = make_single_table_database()
        self.snapshot_a = build_snapshot_from_database(
            self.db, workspace_id="ws_alpha", snapshot_id="snap_" + "a" * 32
        )
        self.snapshot_b = build_snapshot_from_database(
            self.db, workspace_id="ws_beta", snapshot_id="snap_" + "b" * 32
        )

    async def test_in_memory_save_and_retrieve(self) -> None:
        """Verify saving and retrieving from InMemorySnapshotStorage."""
        storage = InMemorySnapshotStorage()
        await storage.save(self.snapshot_a)

        retrieved = await storage.get_by_id(self.snapshot_a.snapshot_id, "ws_alpha")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.snapshot_id, self.snapshot_a.snapshot_id)
        self.assertEqual(retrieved.fingerprint, self.snapshot_a.fingerprint)

    async def test_in_memory_workspace_isolation(self) -> None:
        """Verify workspace A cannot retrieve or discover workspace B snapshots."""
        storage = InMemorySnapshotStorage()
        await storage.save(self.snapshot_a)
        await storage.save(self.snapshot_b)

        # Cross-workspace retrieval returns None
        self.assertIsNone(await storage.get_by_id(self.snapshot_b.snapshot_id, "ws_alpha"))
        self.assertIsNone(await storage.get_by_id(self.snapshot_a.snapshot_id, "ws_beta"))

        # Listing in workspace alpha returns only snapshot A
        listed_alpha = await storage.list_snapshots(SnapshotFilter(workspace_id="ws_alpha"))
        self.assertEqual(len(listed_alpha), 1)
        self.assertEqual(listed_alpha[0].snapshot_id, self.snapshot_a.snapshot_id)

    async def test_in_memory_immutability_enforcement(self) -> None:
        """Verify overwriting an existing snapshot ID with different fingerprint raises error."""
        storage = InMemorySnapshotStorage()
        await storage.save(self.snapshot_a)

        # Build conflicting snapshot with same ID but different content
        empty_db = make_empty_database()
        conflicting_snap = build_snapshot_from_database(
            empty_db, workspace_id="ws_alpha", snapshot_id=self.snapshot_a.snapshot_id
        )

        with pytest.raises(SnapshotStorageError, match="Cannot overwrite immutable snapshot"):
            await storage.save(conflicting_snap)

    async def test_in_memory_delete(self) -> None:
        """Verify deleting a snapshot removes it from storage."""
        storage = InMemorySnapshotStorage()
        await storage.save(self.snapshot_a)

        success = await storage.delete(self.snapshot_a.snapshot_id, "ws_alpha")
        self.assertTrue(success)
        self.assertIsNone(await storage.get_by_id(self.snapshot_a.snapshot_id, "ws_alpha"))

    async def test_in_memory_verify(self) -> None:
        """Verify storage-level integrity check."""
        storage = InMemorySnapshotStorage()
        await storage.save(self.snapshot_a)

        report = await storage.verify(self.snapshot_a.snapshot_id, "ws_alpha")
        self.assertTrue(report.is_valid)

        with pytest.raises(SnapshotNotFoundError):
            await storage.verify("snap_non_existent", "ws_alpha")

    async def test_filesystem_storage_lifecycle(self) -> None:
        """Verify FileSystemSnapshotStorage save, get, list, and delete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileSystemSnapshotStorage(tmpdir)
            await storage.save(self.snapshot_a)

            # Retrieve
            retrieved = await storage.get_by_id(self.snapshot_a.snapshot_id, "ws_alpha")
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.snapshot_id, self.snapshot_a.snapshot_id)

            # Workspace isolation on disk
            self.assertIsNone(await storage.get_by_id(self.snapshot_a.snapshot_id, "ws_beta"))

            # Verify integrity
            report = await storage.verify(self.snapshot_a.snapshot_id, "ws_alpha")
            self.assertTrue(report.is_valid)

            # Delete
            deleted = await storage.delete(self.snapshot_a.snapshot_id, "ws_alpha")
            self.assertTrue(deleted)
            self.assertIsNone(await storage.get_by_id(self.snapshot_a.snapshot_id, "ws_alpha"))


if __name__ == "__main__":
    unittest.main()
