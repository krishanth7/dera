"""Tests for Phase 6.5 End-to-End Reverse Engineering Integration.

Verifies complete flow across the reverse engineering stack:
Canonical Database |
  v
Phase 6.1 Schema Representation |
  v
Phase 6.2 Structural Reconstruction |
  v
Phase 6.3 Foreign Key Relationship Graph |
  v
Phase 6.4 Dependency Analysis & Cycle Detection |
  v
Phase 6.5 Schema Snapshot Builder |
  v
Storage & Integrity Verification
"""

from __future__ import annotations

import unittest

from dera.reverse_engineering.snapshots.integrity import (
    IntegrityVerificationStatus,
    verify_snapshot_integrity,
)
from dera.reverse_engineering.snapshots.models import SchemaSnapshot
from dera.reverse_engineering.snapshots.repository import InMemorySnapshotStorage

from tests.reverse_engineering.phase_6_4.fixtures import (
    make_ecommerce_schema,
    make_mutual_cycle_schema,
    make_self_referencing_schema,
)
from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
)


class TestSnapshotIntegration(unittest.IsolatedAsyncioTestCase):
    """End-to-end integration test suite across reverse engineering phases."""

    async def test_ecommerce_schema_full_integration(self) -> None:
        """Verify full reverse engineering pipeline on comprehensive e-commerce schema."""
        db = make_ecommerce_schema()
        snapshot = build_snapshot_from_database(db, workspace_id="ws_ecom")

        self.assertIsInstance(snapshot, SchemaSnapshot)
        self.assertEqual(snapshot.database_name, "ecommerce_db")
        self.assertEqual(len(snapshot.payload.tables), 7)
        self.assertIsNotNone(snapshot.payload.dependencies)
        self.assertGreater(snapshot.payload.dependencies.total_edges, 0)

        # Integrity verification
        report = verify_snapshot_integrity(snapshot)
        self.assertEqual(report.status, IntegrityVerificationStatus.VALID)
        self.assertTrue(report.is_valid)

        # Storage persistence and retrieval
        storage = InMemorySnapshotStorage()
        await storage.save(snapshot)

        retrieved = await storage.get_by_id(snapshot.snapshot_id, "ws_ecom")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.fingerprint, snapshot.fingerprint)

    async def test_cyclic_schema_integration(self) -> None:
        """Verify snapshot capturing schemas with cyclic dependencies."""
        db = make_mutual_cycle_schema()
        snapshot = build_snapshot_from_database(db, workspace_id="ws_cycle")

        self.assertIsNotNone(snapshot.payload.dependencies)
        self.assertTrue(snapshot.payload.dependencies.has_cycles)
        self.assertGreater(snapshot.payload.dependencies.cycle_count, 0)

        report = verify_snapshot_integrity(snapshot)
        self.assertTrue(report.is_valid)

    async def test_self_referencing_schema_integration(self) -> None:
        """Verify snapshot capturing tables with self-referencing foreign keys."""
        db = make_self_referencing_schema()
        snapshot = build_snapshot_from_database(db, workspace_id="ws_self")

        self.assertIsNotNone(snapshot.payload.dependencies)
        self.assertTrue(snapshot.payload.dependencies.has_cycles)

        report = verify_snapshot_integrity(snapshot)
        self.assertTrue(report.is_valid)


if __name__ == "__main__":
    unittest.main()
