"""Small deterministic immutable snapshots for SQL diagnostics tests."""

from datetime import UTC, datetime

from dera.metadata.enums import CanonicalTypeCategory
from dera.reverse_engineering.snapshots.fingerprints import compute_structural_fingerprint
from dera.reverse_engineering.snapshots.models import (
    SchemaSnapshot,
    SnapshotColumnPayload,
    SnapshotEnvelope,
    SnapshotForeignKeyPayload,
    SnapshotIndexPayload,
    SnapshotStructuralPayload,
    SnapshotTablePayload,
)
from dera.reverse_engineering.snapshots.provenance import SnapshotProvenance


def snapshot(workspace="ws_test", engine="postgresql", indexed=True, complete="COMPLETE"):
    def table(name, category):
        return SnapshotTablePayload(
            table_id=f"t_{name}",
            namespace="public",
            name=name,
            columns=(
                SnapshotColumnPayload(
                    column_id=f"c_{name}",
                    name="id",
                    ordinal_position=1,
                    native_data_type="integer" if category == "INTEGER" else "text",
                    canonical_type=CanonicalTypeCategory(category),
                ),
            ),
            indexes=(
                SnapshotIndexPayload(index_id=f"i_{name}", name=f"idx_{name}", columns=("id",)),
            )
            if indexed
            else (),
            foreign_keys=(
                SnapshotForeignKeyPayload(
                    constraint_id="fk_id",
                    name="fk_accounts_users",
                    source_columns=("id",),
                    target_namespace="public",
                    target_table="users",
                    target_columns=("id",),
                ),
            )
            if name == "accounts"
            else (),
        )

    payload = SnapshotStructuralPayload(
        database_name="test",
        engine=engine,
        namespaces=("public",),
        tables=(table("accounts", "INTEGER"), table("users", "TEXT")),
        completeness=complete,
    )
    envelope = SnapshotEnvelope(
        snapshot_id="snap_test",
        workspace_id=workspace,
        database_id="db_test",
        source_reference="test",
        capture_timestamp=datetime(2026, 11, 2, tzinfo=UTC),
        provenance=SnapshotProvenance(engine=engine, source_reference="test"),
    )
    return SchemaSnapshot(
        snapshot_id="snap_test",
        fingerprint=compute_structural_fingerprint(payload),
        envelope=envelope,
        payload=payload,
    )
