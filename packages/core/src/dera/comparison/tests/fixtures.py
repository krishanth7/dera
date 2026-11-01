"""DERA Comparison — Phase 9.1 Test Fixtures & Snapshot Generators.

Provides deterministic snapshot builders, baseline/target test schemas,
and modified fixtures across tables, columns, constraints, indexes, views, and engines.
"""

from __future__ import annotations

from datetime import UTC, datetime

from dera.metadata.enums import (
    CanonicalTypeCategory,
    ForeignKeyAction,
    MetadataCompleteness,
    TableType,
)
from dera.metadata.identity import compute_stable_object_id
from dera.reverse_engineering.snapshots.fingerprints import compute_structural_fingerprint
from dera.reverse_engineering.snapshots.models import (
    SNAPSHOT_FORMAT_VERSION,
    SchemaSnapshot,
    SnapshotCheckConstraintPayload,
    SnapshotColumnPayload,
    SnapshotEnvelope,
    SnapshotForeignKeyPayload,
    SnapshotIndexPayload,
    SnapshotPrimaryKeyPayload,
    SnapshotRelationshipPayload,
    SnapshotStructuralPayload,
    SnapshotTablePayload,
    SnapshotUniqueConstraintPayload,
    SnapshotViewPayload,
)
from dera.reverse_engineering.snapshots.provenance import SnapshotProvenance


def make_test_envelope(
    snapshot_id: str = "snap_baseline",
    workspace_id: str = "ws_test_tenant",
    source_ref: str = "test_catalog",
) -> SnapshotEnvelope:
    """Generate a valid SnapshotEnvelope with fixed UTC timestamp for testing."""
    return SnapshotEnvelope(
        snapshot_id=snapshot_id,
        workspace_id=workspace_id,
        database_id="db_canonical_01",
        source_reference=source_ref,
        capture_timestamp=datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC),
        provenance=SnapshotProvenance(
            engine="postgresql",
            engine_version="16.0",
            source_reference=source_ref,
            completeness=MetadataCompleteness.COMPLETE,
        ),
        validation_status="VALID",
        tags={"env": "test"},
    )


def make_test_column(
    table_id: str,
    name: str,
    ordinal: int,
    native_type: str = "integer",
    canonical_type: CanonicalTypeCategory = CanonicalTypeCategory.INTEGER,
    is_nullable: bool = False,
    default_expression: str | None = None,
    comment: str | None = None,
) -> SnapshotColumnPayload:
    col_id = compute_stable_object_id(
        kind="column",
        parent_id=table_id,
        native_name=name,
    )
    return SnapshotColumnPayload(
        column_id=col_id,
        name=name,
        ordinal_position=ordinal,
        native_data_type=native_type,
        canonical_type=canonical_type,
        is_nullable=is_nullable,
        default_expression=default_expression,
        comment=comment,
    )


def make_test_table(
    namespace: str,
    name: str,
    columns: tuple[SnapshotColumnPayload, ...] = (),
    primary_key: SnapshotPrimaryKeyPayload | None = None,
    foreign_keys: tuple[SnapshotForeignKeyPayload, ...] = (),
    unique_constraints: tuple[SnapshotUniqueConstraintPayload, ...] = (),
    check_constraints: tuple[SnapshotCheckConstraintPayload, ...] = (),
    indexes: tuple[SnapshotIndexPayload, ...] = (),
    table_type: TableType = TableType.TABLE,
    comment: str | None = None,
) -> SnapshotTablePayload:
    table_id = compute_stable_object_id(
        kind="table",
        namespace=namespace,
        native_name=name,
    )
    return SnapshotTablePayload(
        table_id=table_id,
        namespace=namespace,
        name=name,
        table_type=table_type,
        columns=columns,
        primary_key=primary_key,
        foreign_keys=foreign_keys,
        unique_constraints=unique_constraints,
        check_constraints=check_constraints,
        indexes=indexes,
        comment=comment,
    )


def build_snapshot_from_payload(
    payload: SnapshotStructuralPayload,
    snapshot_id: str = "snap_001",
    workspace_id: str = "ws_test_tenant",
) -> SchemaSnapshot:
    """Build a valid SchemaSnapshot by computing its cryptographic structural fingerprint."""
    fp = compute_structural_fingerprint(payload)
    envelope = make_test_envelope(snapshot_id=snapshot_id, workspace_id=workspace_id)
    return SchemaSnapshot(
        format_version=SNAPSHOT_FORMAT_VERSION,
        snapshot_id=snapshot_id,
        fingerprint=fp,
        envelope=envelope,
        payload=payload,
    )


def make_standard_ecommerce_payload(
    engine: str = "postgresql",
    completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE,
) -> SnapshotStructuralPayload:
    """Standard baseline ecommerce schema with users, orders, order_items tables."""
    # 1. Users table
    users_id = compute_stable_object_id(kind="table", namespace="public", native_name="users")
    users_cols = (
        make_test_column(users_id, "id", 1, "integer", CanonicalTypeCategory.INTEGER, False),
        make_test_column(users_id, "email", 2, "varchar(255)", CanonicalTypeCategory.TEXT, False),
        make_test_column(users_id, "name", 3, "text", CanonicalTypeCategory.TEXT, True),
        make_test_column(
            users_id,
            "created_at",
            4,
            "timestamptz",
            CanonicalTypeCategory.TIMESTAMP,
            False,
            default_expression="NOW()",
        ),
    )
    users_pk = SnapshotPrimaryKeyPayload(
        constraint_id=compute_stable_object_id(
            kind="primary_key", parent_id=users_id, native_name="pk_users"
        ),
        name="pk_users",
        columns=("id",),
    )
    users_idx = (
        SnapshotIndexPayload(
            index_id=compute_stable_object_id(
                kind="index", parent_id=users_id, native_name="idx_users_email"
            ),
            name="idx_users_email",
            columns=("email",),
            is_unique=True,
            index_type="BTREE",
        ),
    )
    users_table = make_test_table(
        namespace="public",
        name="users",
        columns=users_cols,
        primary_key=users_pk,
        indexes=users_idx,
    )

    # 2. Orders table
    orders_id = compute_stable_object_id(kind="table", namespace="public", native_name="orders")
    orders_cols = (
        make_test_column(orders_id, "id", 1, "integer", CanonicalTypeCategory.INTEGER, False),
        make_test_column(orders_id, "user_id", 2, "integer", CanonicalTypeCategory.INTEGER, False),
        make_test_column(
            orders_id,
            "status",
            3,
            "varchar(50)",
            CanonicalTypeCategory.TEXT,
            False,
            default_expression="'pending'",
        ),
        make_test_column(
            orders_id,
            "total",
            4,
            "numeric(10,2)",
            CanonicalTypeCategory.DECIMAL,
            False,
            default_expression="0.00",
        ),
    )
    orders_pk = SnapshotPrimaryKeyPayload(
        constraint_id=compute_stable_object_id(
            kind="primary_key", parent_id=orders_id, native_name="pk_orders"
        ),
        name="pk_orders",
        columns=("id",),
    )
    orders_fk = (
        SnapshotForeignKeyPayload(
            constraint_id=compute_stable_object_id(
                kind="foreign_key", parent_id=orders_id, native_name="fk_orders_user"
            ),
            name="fk_orders_user",
            source_columns=("user_id",),
            target_namespace="public",
            target_table="users",
            target_columns=("id",),
            on_delete=ForeignKeyAction.CASCADE,
            on_update=ForeignKeyAction.NO_ACTION,
        ),
    )
    orders_chk = (
        SnapshotCheckConstraintPayload(
            constraint_id=compute_stable_object_id(
                kind="check_constraint", parent_id=orders_id, native_name="chk_orders_total"
            ),
            name="chk_orders_total",
            expression="total >= 0",
        ),
    )
    orders_table = make_test_table(
        namespace="public",
        name="orders",
        columns=orders_cols,
        primary_key=orders_pk,
        foreign_keys=orders_fk,
        check_constraints=orders_chk,
    )

    # Relationship edge
    rel_edge = SnapshotRelationshipPayload(
        edge_id="rel_orders_to_users",
        source_table_id=orders_id,
        target_table_id=users_id,
        constraint_name="fk_orders_user",
        source_columns=("user_id",),
        target_columns=("id",),
    )

    # View
    vw_id = compute_stable_object_id(kind="view", namespace="public", native_name="v_active_orders")
    active_orders_view = SnapshotViewPayload(
        view_id=vw_id,
        namespace="public",
        name="v_active_orders",
        definition="SELECT * FROM orders WHERE status != 'cancelled'",
        is_materialized=False,
    )

    return SnapshotStructuralPayload(
        schema_format="dera.structural.v1",
        database_name="shop_db",
        engine=engine,
        engine_version="16.0",
        namespaces=("public",),
        tables=(orders_table, users_table),
        views=(active_orders_view,),
        relationships=(rel_edge,),
        completeness=completeness,
    )
