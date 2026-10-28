"""Tests for Phase 6.5 Snapshot Domain Models.

Verifies:
- Frozen immutability on models and structural payloads.
- Extra field rejection (extra="forbid").
- Required field validations and defaults.
- Property accessors on SchemaSnapshot.
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

import pytest
from dera.metadata.enums import CanonicalTypeCategory, MetadataCompleteness, TableType
from dera.reverse_engineering.snapshots.models import (
    FINGERPRINT_ALGORITHM_NAME,
    FINGERPRINT_DOMAIN,
    SNAPSHOT_FORMAT_VERSION,
    SchemaSnapshot,
    SnapshotColumnPayload,
    SnapshotEnvelope,
    SnapshotStructuralPayload,
    SnapshotTablePayload,
)
from dera.reverse_engineering.snapshots.provenance import SnapshotProvenance
from pydantic import ValidationError


class TestSnapshotModels(unittest.TestCase):
    """Test suite for snapshot Pydantic domain models."""

    def setUp(self) -> None:
        self.column = SnapshotColumnPayload(
            column_id="col:1",
            name="id",
            ordinal_position=1,
            native_data_type="integer",
            canonical_type=CanonicalTypeCategory.INTEGER,
            is_nullable=False,
        )
        self.table = SnapshotTablePayload(
            table_id="tbl:1",
            namespace="public",
            name="users",
            table_type=TableType.TABLE,
            columns=(self.column,),
        )
        self.payload = SnapshotStructuralPayload(
            database_name="test_db",
            engine="postgresql",
            namespaces=("public",),
            tables=(self.table,),
            completeness=MetadataCompleteness.COMPLETE,
        )
        self.provenance = SnapshotProvenance(
            engine="postgresql",
            engine_version="16.0",
            source_reference="test_ref",
        )
        self.envelope = SnapshotEnvelope(
            snapshot_id="snap_1234567890abcdef1234567890abcdef",
            workspace_id="ws_default",
            database_id="db:1",
            source_reference="test_ref",
            capture_timestamp=datetime(2026, 10, 28, 12, 0, 0, tzinfo=UTC),
            provenance=self.provenance,
        )
        self.snapshot = SchemaSnapshot(
            snapshot_id="snap_1234567890abcdef1234567890abcdef",
            fingerprint="a" * 64,
            envelope=self.envelope,
            payload=self.payload,
        )

    def test_schema_snapshot_defaults(self) -> None:
        """Verify default versions, domains, and algorithm names."""
        self.assertEqual(self.snapshot.format_version, SNAPSHOT_FORMAT_VERSION)
        self.assertEqual(self.snapshot.fingerprint_algorithm, FINGERPRINT_ALGORITHM_NAME)
        self.assertEqual(self.snapshot.fingerprint_domain, FINGERPRINT_DOMAIN)
        self.assertEqual(self.snapshot.database_name, "test_db")
        self.assertEqual(self.snapshot.engine, "postgresql")
        self.assertEqual(self.snapshot.workspace_id, "ws_default")
        self.assertEqual(self.snapshot.completeness, MetadataCompleteness.COMPLETE)

    def test_immutability_enforced(self) -> None:
        """Verify frozen models prohibit field reassignment."""
        with pytest.raises(ValidationError):
            self.snapshot.fingerprint = "b" * 64  # type: ignore[misc]

        with pytest.raises(ValidationError):
            self.column.name = "new_name"  # type: ignore[misc]

        with pytest.raises(ValidationError):
            self.payload.database_name = "mutated_db"  # type: ignore[misc]

        with pytest.raises(ValidationError):
            self.envelope.workspace_id = "other_ws"  # type: ignore[misc]

    def test_extra_fields_forbidden(self) -> None:
        """Verify extra='forbid' prevents unrecognized fields."""
        with pytest.raises(ValidationError):
            SnapshotColumnPayload(
                column_id="col:2",
                name="name",
                ordinal_position=2,
                native_data_type="varchar",
                canonical_type=CanonicalTypeCategory.TEXT,
                unrecognized_field="illegal",  # type: ignore[call-arg]
            )

        with pytest.raises(ValidationError):
            SnapshotStructuralPayload(
                database_name="db",
                engine="sqlite",
                extra_attribute="not_allowed",  # type: ignore[call-arg]
            )


if __name__ == "__main__":
    unittest.main()
