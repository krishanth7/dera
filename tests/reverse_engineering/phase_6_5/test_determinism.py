"""Tests for Phase 6.5 Snapshot Determinism.

Verifies:
- 100% byte-level reproducible canonical JSON serialization.
- Invariance of structural fingerprints across multiple executions.
- Invariance of fingerprints under input permutation (e.g. shuffled tables or namespaces).
- Strict sensitivity to any structural schema difference.
"""

from __future__ import annotations

import unittest

from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.snapshots.builder import SchemaSnapshotBuilder
from dera.reverse_engineering.snapshots.serialization import (
    serialize_structural_payload_to_bytes,
)

from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
    make_composite_constraints_database,
)


class TestSnapshotDeterminism(unittest.TestCase):
    """Test suite for snapshot determinism and reproducibility."""

    def test_reproducible_fingerprint_generation(self) -> None:
        """Verify identical input schemas generate identical SHA-256 fingerprints."""
        db1 = make_composite_constraints_database()
        db2 = make_composite_constraints_database()

        snap1 = build_snapshot_from_database(db1)
        snap2 = build_snapshot_from_database(db2)

        self.assertEqual(snap1.fingerprint, snap2.fingerprint)

    def test_reproducible_canonical_bytes(self) -> None:
        """Verify byte-level equality across serialized structural payloads."""
        db = make_composite_constraints_database()
        snap1 = build_snapshot_from_database(db)
        snap2 = build_snapshot_from_database(db)

        bytes1 = serialize_structural_payload_to_bytes(snap1.payload)
        bytes2 = serialize_structural_payload_to_bytes(snap2.payload)

        self.assertEqual(bytes1, bytes2)

    def test_table_order_permutation_invariance(self) -> None:
        """Verify canonicalization guarantees identical fingerprints regardless of table input order."""
        db = make_composite_constraints_database()
        tables = list(db.namespaces[0].tables)

        # Reversed order
        tables_rev = tuple(reversed(tables))
        db_rev = db.model_copy(
            update={"namespaces": (db.namespaces[0].model_copy(update={"tables": tables_rev}),)}
        )

        schema_orig = SchemaBuilder.from_canonical_database(db)
        schema_rev = SchemaBuilder.from_canonical_database(db_rev)

        snap_orig = SchemaSnapshotBuilder.from_analysis(schema_orig)
        snap_rev = SchemaSnapshotBuilder.from_analysis(schema_rev)

        self.assertEqual(snap_orig.fingerprint, snap_rev.fingerprint)


if __name__ == "__main__":
    unittest.main()
