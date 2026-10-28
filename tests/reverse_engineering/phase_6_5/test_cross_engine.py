"""Tests for Phase 6.5 Cross-Engine Snapshot Compatibility.

Verifies:
- Snapshot building across PostgreSQL, SQLite, MySQL, and MariaDB.
- Engine type preservation in structural payload.
- Engine differentiation: same table name on different engines produces engine-specific fingerprints.
- Integrity verification succeeds across all engines.
"""

from __future__ import annotations

import unittest

from dera.reverse_engineering.snapshots.integrity import (
    IntegrityVerificationStatus,
    verify_snapshot_integrity,
)

from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
    make_single_table_database,
)


class TestSnapshotCrossEngine(unittest.TestCase):
    """Test suite for multi-engine snapshot behavior."""

    def test_multi_engine_snapshot_construction(self) -> None:
        """Verify snapshot construction across all supported database engines."""
        engines = ("postgresql", "sqlite", "mysql", "mariadb")
        snapshots = {}

        for eng in engines:
            db = make_single_table_database(name="shared_db", engine=eng)
            snap = build_snapshot_from_database(db)

            self.assertEqual(snap.engine, eng)
            self.assertEqual(snap.payload.engine, eng)

            # Integrity verification
            report = verify_snapshot_integrity(snap)
            self.assertEqual(report.status, IntegrityVerificationStatus.VALID)

            snapshots[eng] = snap

        # Distinct engines produce distinct fingerprints due to engine binding
        fps = {snap.fingerprint for snap in snapshots.values()}
        self.assertEqual(len(fps), len(engines))


if __name__ == "__main__":
    unittest.main()
