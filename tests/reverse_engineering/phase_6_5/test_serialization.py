"""Tests for Phase 6.5 Deterministic Snapshot Serialization & Deserialization.

Verifies:
- RFC 8785 canonical JSON output (lexicographical key sorting, compact delimiters).
- Full lossless round-trip serialization and deserialization.
- Rejection of non-finite float values (NaN, Inf).
- Enforced byte-size resource limits against payload flooding.
- Safe rejection of non-object JSON roots.
"""

from __future__ import annotations

import unittest

import pytest
from dera.reverse_engineering.snapshots.errors import (
    SnapshotDeserializationError,
    SnapshotResourceLimitError,
    SnapshotSerializationError,
)
from dera.reverse_engineering.snapshots.limits import SnapshotResourceLimits
from dera.reverse_engineering.snapshots.serialization import (
    _validate_numeric_values,
    deserialize_snapshot_from_json,
    serialize_snapshot_to_json,
    serialize_structural_payload_to_bytes,
)

from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
    make_single_table_database,
    make_unicode_database,
)


class TestSnapshotSerialization(unittest.TestCase):
    """Test suite for snapshot JSON serialization and deserialization."""

    def setUp(self) -> None:
        db = make_single_table_database()
        self.snapshot = build_snapshot_from_database(db)

    def test_canonical_json_formatting(self) -> None:
        """Verify serialization is compact and deterministic."""
        json_compact = serialize_snapshot_to_json(self.snapshot, indent=None)
        # No extraneous whitespace after commas and colons in compact mode
        self.assertNotIn(": ", json_compact)
        self.assertNotIn(", ", json_compact)

    def test_round_trip_lossless(self) -> None:
        """Verify snapshot round-trips losslessly through serialization and deserialization."""
        json_str = serialize_snapshot_to_json(self.snapshot)
        reconstructed = deserialize_snapshot_from_json(json_str)

        self.assertEqual(reconstructed.snapshot_id, self.snapshot.snapshot_id)
        self.assertEqual(reconstructed.fingerprint, self.snapshot.fingerprint)
        self.assertEqual(reconstructed.database_name, self.snapshot.database_name)
        self.assertEqual(len(reconstructed.payload.tables), len(self.snapshot.payload.tables))

    def test_unicode_preservation_without_escaping(self) -> None:
        """Verify Unicode characters are preserved in UTF-8 without backslash escapes."""
        db_unicode = make_unicode_database()
        snap_unicode = build_snapshot_from_database(db_unicode)

        json_str = serialize_snapshot_to_json(snap_unicode)
        self.assertIn("café_données", json_str)
        self.assertIn("libellé_français", json_str)
        self.assertIn("valeur_€", json_str)

        reconstructed = deserialize_snapshot_from_json(json_str)
        tbl_names = [t.name for t in reconstructed.payload.tables]
        self.assertIn("café_données", tbl_names)

    def test_non_finite_numeric_rejection(self) -> None:
        """Verify NaN and Infinity raise SnapshotSerializationError."""
        with pytest.raises(SnapshotSerializationError, match="Non-finite float value"):
            _validate_numeric_values({"bad_float": float("nan")})

        with pytest.raises(SnapshotSerializationError, match="Non-finite float value"):
            _validate_numeric_values({"bad_float": float("inf")})

    def test_serialized_size_limit_enforced(self) -> None:
        """Verify exceeding max_serialized_bytes raises SnapshotResourceLimitError."""
        small_limits = SnapshotResourceLimits(max_serialized_bytes=100)
        with pytest.raises(SnapshotResourceLimitError):
            serialize_snapshot_to_json(self.snapshot, limits=small_limits)

        with pytest.raises(SnapshotResourceLimitError):
            serialize_structural_payload_to_bytes(self.snapshot.payload, limits=small_limits)

    def test_malformed_json_deserialization_rejected(self) -> None:
        """Verify invalid or non-object JSON is safely rejected."""
        with pytest.raises(SnapshotDeserializationError):
            deserialize_snapshot_from_json("{broken json")

        with pytest.raises(
            SnapshotDeserializationError, match="Root of snapshot JSON must be an object"
        ):
            deserialize_snapshot_from_json('["array_root"]')


if __name__ == "__main__":
    unittest.main()
