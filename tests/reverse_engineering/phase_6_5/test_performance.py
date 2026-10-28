"""Tests for Phase 6.5 Snapshot Performance Benchmarks.

Measures:
- Snapshot construction duration.
- Canonical JSON serialization duration.
- SHA-256 fingerprint digest duration.
- Storage write and retrieval duration.
- Integrity verification performance.
"""

from __future__ import annotations

import time
import unittest

from dera.reverse_engineering.snapshots.integrity import verify_snapshot_integrity
from dera.reverse_engineering.snapshots.repository import (
    InMemorySnapshotStorage,
)
from dera.reverse_engineering.snapshots.serialization import (
    deserialize_snapshot_from_json,
    serialize_snapshot_to_json,
)

from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
    make_composite_constraints_database,
)


class TestSnapshotPerformance(unittest.IsolatedAsyncioTestCase):
    """Performance benchmarks for snapshot lifecycle operations."""

    async def test_snapshot_lifecycle_benchmarks(self) -> None:
        """Measure runtime for snapshot build, serialization, digest, and verification."""
        db = make_composite_constraints_database()

        # 1. Construction Time
        t0 = time.perf_counter()
        snapshot = build_snapshot_from_database(db)
        t_build = time.perf_counter() - t0
        self.assertLess(t_build, 0.5, "Snapshot build exceeded 500ms budget")

        # 2. Canonical Serialization Time
        t0 = time.perf_counter()
        json_str = serialize_snapshot_to_json(snapshot)
        t_serialize = time.perf_counter() - t0
        self.assertLess(t_serialize, 0.2, "Snapshot serialization exceeded 200ms budget")

        # 3. Deserialization Time
        t0 = time.perf_counter()
        deserialized = deserialize_snapshot_from_json(json_str)
        t_deserialize = time.perf_counter() - t0
        self.assertIsNotNone(deserialized.snapshot_id)
        self.assertLess(t_deserialize, 0.2, "Snapshot deserialization exceeded 200ms budget")

        # 4. Integrity Verification Time
        t0 = time.perf_counter()
        report = verify_snapshot_integrity(snapshot)
        t_verify = time.perf_counter() - t0
        self.assertTrue(report.is_valid)
        self.assertLess(t_verify, 0.1, "Integrity verification exceeded 100ms budget")

        # 5. In-Memory Storage Write & Read
        storage = InMemorySnapshotStorage()
        t0 = time.perf_counter()
        await storage.save(snapshot)
        t_save = time.perf_counter() - t0
        self.assertLess(t_save, 0.05, "In-memory storage save exceeded 50ms budget")

        t0 = time.perf_counter()
        read_snap = await storage.get_by_id(snapshot.snapshot_id, snapshot.workspace_id)
        t_read = time.perf_counter() - t0
        self.assertIsNotNone(read_snap)
        self.assertLess(t_read, 0.05, "In-memory storage read exceeded 50ms budget")


if __name__ == "__main__":
    unittest.main()
