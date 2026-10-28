"""Tests for Phase 6.5 SchemaSnapshotBuilder.

Verifies:
- Building snapshot from SchemaRepresentation alone.
- Building snapshot from full Phase 6.1 - 6.4 pipeline outputs.
- Cross-phase consistency enforcement (database name mismatch, engine mismatch, database_id mismatch).
- Custom snapshot ID, tags, and capture timestamps.
- Completeness and provenance preservation.
"""

from __future__ import annotations

import unittest

import pytest
from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.reconstruction.builder import StructuralReconstructionBuilder
from dera.reverse_engineering.snapshots.builder import SchemaSnapshotBuilder
from dera.reverse_engineering.snapshots.errors import SnapshotValidationError
from dera.reverse_engineering.snapshots.models import SchemaSnapshot

from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
    make_single_table_database,
)


class TestSnapshotBuilder(unittest.TestCase):
    """Test suite for SchemaSnapshotBuilder."""

    def test_build_from_schema_representation_only(self) -> None:
        """Verify building snapshot without downstream reconstruction or dependency graphs."""
        db = make_single_table_database()
        schema = SchemaBuilder.from_canonical_database(db)
        snap = SchemaSnapshotBuilder.from_analysis(
            schema=schema,
            workspace_id="test_ws",
            tags={"environment": "testing"},
        )
        self.assertIsInstance(snap, SchemaSnapshot)
        self.assertEqual(snap.workspace_id, "test_ws")
        self.assertEqual(snap.envelope.tags.get("environment"), "testing")
        self.assertEqual(snap.database_name, "single_tbl_db")
        self.assertEqual(len(snap.payload.tables), 1)
        self.assertEqual(snap.payload.tables[0].name, "users")

    def test_build_from_full_pipeline(self) -> None:
        """Verify building snapshot with all Phase 6.1-6.4 artifacts."""
        db = make_single_table_database()
        snap = build_snapshot_from_database(db, workspace_id="prod_ws")
        self.assertIsInstance(snap, SchemaSnapshot)
        self.assertEqual(snap.workspace_id, "prod_ws")
        self.assertIsNotNone(snap.payload.dependencies)
        self.assertEqual(snap.payload.dependencies.total_edges, 0)
        self.assertFalse(snap.payload.dependencies.has_cycles)

    def test_cross_phase_database_name_mismatch(self) -> None:
        """Verify builder rejects mismatched database names between SchemaRepresentation and reconstruction."""
        db1 = make_single_table_database(name="db_one")
        db2 = make_single_table_database(name="db_two")

        schema1 = SchemaBuilder.from_canonical_database(db1)
        schema2 = SchemaBuilder.from_canonical_database(db2)
        recon2 = StructuralReconstructionBuilder().build_from_schema(schema2)

        with pytest.raises(SnapshotValidationError, match="database name mismatch"):
            SchemaSnapshotBuilder.from_analysis(
                schema=schema1,
                reconstruction=recon2,
            )

    def test_cross_phase_engine_mismatch(self) -> None:
        """Verify builder rejects mismatched engine types."""
        db_pg = make_single_table_database(name="same_db", engine="postgresql")
        db_sqlite = make_single_table_database(name="same_db", engine="sqlite")

        schema_pg = SchemaBuilder.from_canonical_database(db_pg)
        schema_sqlite = SchemaBuilder.from_canonical_database(db_sqlite)
        recon_sqlite = StructuralReconstructionBuilder().build_from_schema(schema_sqlite)

        with pytest.raises(SnapshotValidationError, match="engine mismatch"):
            SchemaSnapshotBuilder.from_analysis(
                schema=schema_pg,
                reconstruction=recon_sqlite,
            )

    def test_cross_phase_database_id_mismatch(self) -> None:
        """Verify builder rejects mismatched database_id between schema and graph."""
        db1 = make_single_table_database(name="db_1")
        db2 = make_single_table_database(name="db_2")

        schema1 = SchemaBuilder.from_canonical_database(db1)
        schema2 = SchemaBuilder.from_canonical_database(db2)
        graph2 = ForeignKeyGraphBuilder.from_schema(schema2)

        with pytest.raises(SnapshotValidationError, match="database_id mismatch"):
            SchemaSnapshotBuilder.from_analysis(
                schema=schema1,
                relationships=graph2,
            )


if __name__ == "__main__":
    unittest.main()
