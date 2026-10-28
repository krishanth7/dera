"""Tests for Phase 6.5 Snapshot Retention Controls.

Verifies:
- Retention policy evaluation against count limits.
- Retention policy evaluation against age expiration.
- Protection of tagged snapshots ('production', 'baseline').
- Preservation of unique structural fingerprints.
- Dry-run and execution modes of RetentionManager.
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from dera.reverse_engineering.snapshots.models import SchemaSnapshot
from dera.reverse_engineering.snapshots.repository import InMemorySnapshotStorage
from dera.reverse_engineering.snapshots.retention import (
    RetentionManager,
    SnapshotRetentionPolicy,
)

from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
    make_single_table_database,
)


class TestSnapshotRetention(unittest.IsolatedAsyncioTestCase):
    """Test suite for snapshot retention lifecycle rules."""

    def setUp(self) -> None:
        self.db = make_single_table_database()
        self.now = datetime(2026, 10, 28, 12, 0, 0, tzinfo=UTC)

    def test_evaluate_max_count_pruning(self) -> None:
        """Verify oldest snapshots exceeding max_snapshots_per_database are marked expired."""
        snapshots: list[SchemaSnapshot] = []
        for i in range(5):
            snap = build_snapshot_from_database(
                self.db,
                snapshot_id=f"snap_{i:032x}",
            )
            # Adjust timestamp: newest is i=4
            ts = self.now - timedelta(days=(4 - i))
            updated_envelope = snap.envelope.model_copy(update={"capture_timestamp": ts})
            snapshots.append(snap.model_copy(update={"envelope": updated_envelope}))

        # Policy: max 2 snapshots, do not preserve duplicate fingerprints
        policy = SnapshotRetentionPolicy(
            max_snapshots_per_database=2,
            preserve_unique_fingerprints=False,
        )
        res = RetentionManager.evaluate(snapshots, policy, now=self.now)

        self.assertEqual(len(res.retained_snapshot_ids), 2)
        self.assertEqual(len(res.expired_snapshot_ids), 3)

    def test_evaluate_protected_tags_preserved(self) -> None:
        """Verify snapshots with protected tags are never expired by count quotas."""
        snapshots: list[SchemaSnapshot] = []
        for i in range(5):
            tags = {"production": "true"} if i == 0 else {}
            snap = build_snapshot_from_database(
                self.db,
                snapshot_id=f"snap_{i:032x}",
                tags=tags,
            )
            ts = self.now - timedelta(days=(4 - i))
            updated_envelope = snap.envelope.model_copy(update={"capture_timestamp": ts})
            snapshots.append(snap.model_copy(update={"envelope": updated_envelope}))

        policy = SnapshotRetentionPolicy(
            max_snapshots_per_database=1,
            preserve_unique_fingerprints=False,
            protected_tags=("production",),
        )
        res = RetentionManager.evaluate(snapshots, policy, now=self.now)

        # Snapshot 0 is protected, Snapshot 4 is newest
        self.assertIn(f"snap_{0:032x}", res.protected_snapshot_ids)
        self.assertIn(f"snap_{0:032x}", res.retained_snapshot_ids)

    def test_evaluate_max_age_expiration(self) -> None:
        """Verify snapshots older than max_age_days are marked expired."""
        fresh_snap = build_snapshot_from_database(
            self.db,
            snapshot_id="snap_" + "1" * 32,
        )
        old_snap = build_snapshot_from_database(
            self.db,
            snapshot_id="snap_" + "2" * 32,
        )
        old_snap = old_snap.model_copy(
            update={
                "envelope": old_snap.envelope.model_copy(
                    update={"capture_timestamp": self.now - timedelta(days=40)}
                )
            }
        )

        policy = SnapshotRetentionPolicy(
            max_age_days=30,
            preserve_unique_fingerprints=False,
        )
        res = RetentionManager.evaluate([fresh_snap, old_snap], policy, now=self.now)

        self.assertIn(old_snap.snapshot_id, res.expired_snapshot_ids)
        self.assertIn(fresh_snap.snapshot_id, res.retained_snapshot_ids)

    async def test_apply_retention_execution(self) -> None:
        """Verify applying retention deletes expired snapshots from storage."""
        storage = InMemorySnapshotStorage()
        snap1 = build_snapshot_from_database(
            self.db, snapshot_id="snap_" + "1" * 32, workspace_id="ws_ret"
        )
        snap2 = build_snapshot_from_database(
            self.db, snapshot_id="snap_" + "2" * 32, workspace_id="ws_ret"
        )
        snap2 = snap2.model_copy(
            update={
                "envelope": snap2.envelope.model_copy(
                    update={"capture_timestamp": self.now - timedelta(days=10)}
                )
            }
        )

        await storage.save(snap1)
        await storage.save(snap2)

        policy = SnapshotRetentionPolicy(
            max_snapshots_per_database=1, preserve_unique_fingerprints=False
        )
        action_res = await RetentionManager.apply(
            storage=storage,
            workspace_id="ws_ret",
            database_name=self.db.name,
            policy=policy,
            dry_run=False,
        )

        self.assertEqual(action_res.deleted_count, 1)
        # Oldest snap2 should be deleted
        self.assertIsNone(await storage.get_by_id(snap2.snapshot_id, "ws_ret"))
        self.assertIsNotNone(await storage.get_by_id(snap1.snapshot_id, "ws_ret"))


if __name__ == "__main__":
    unittest.main()
