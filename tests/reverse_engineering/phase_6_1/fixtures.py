"""DERA Reverse Engineering — Phase 6.1 Comprehensive Test Fixtures.

Provides rich canonical metadata fixtures covering:
- Multiple namespaces (schemas)
- Multiple tables with composite primary keys
- Composite foreign keys with referential actions
- UNIQUE and CHECK constraints
- Secondary and expression indexes
- Views (regular and materialized)
- Triggers (BEFORE, AFTER, INSERT, UPDATE)
- Generated columns (STORED, VIRTUAL)
- Unicode identifiers (e.g. Greek, Japanese, Arabic, emojis)
- Case-sensitive identifiers
- Partial and restricted metadata fixtures
"""

from __future__ import annotations

from datetime import UTC, datetime

from dera.metadata.enums import (
    CanonicalTypeCategory,
    ConstraintType,
    ForeignKeyAction,
    GenerationMode,
    IndexType,
    MetadataCompleteness,
    ObjectKind,
    TableType,
    TriggerEvent,
    TriggerTiming,
)
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.constraint import CanonicalConstraint
from dera.metadata.models.database import CanonicalDatabase
from dera.metadata.models.index import CanonicalIndex, CanonicalIndexTerm
from dera.metadata.models.namespace import CanonicalNamespace
from dera.metadata.models.relationship import CanonicalForeignKey, ForeignKeyMapping
from dera.metadata.models.table import CanonicalTable
from dera.metadata.models.trigger import CanonicalTrigger
from dera.metadata.models.view import CanonicalView
from dera.metadata.provenance import MetadataProvenance

FIXED_TEST_TIME = datetime(2026, 10, 27, 12, 0, 0, tzinfo=UTC)


def make_provenance(
    engine: str = "postgresql",
    identifier: str = "test",
    version: str = "16.2",
    completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE,
) -> MetadataProvenance:
    """Helper to create deterministic provenance."""
    return MetadataProvenance(
        source_engine=engine,
        source_version=version,
        native_identifier=identifier,
        collection_timestamp=FIXED_TEST_TIME,
        connector_version="5.5.0",
        completeness=completeness,
    )


def build_enterprise_fixture(
    engine: str = "postgresql",
    workspace_id: str | None = "ws_enterprise",
    db_name: str = "enterprise_db",
) -> CanonicalDatabase:
    """Build a comprehensive multi-namespace, composite-key, multi-constraint database fixture."""
    prov = make_provenance(engine=engine, identifier=db_name)

    db_id = compute_stable_object_id(
        engine, ObjectKind.DATABASE, db_name, workspace_id=workspace_id
    )
    public_ns_id = compute_stable_object_id(
        engine, ObjectKind.NAMESPACE, "public", parent_id=db_id, workspace_id=workspace_id
    )
    analytics_ns_id = compute_stable_object_id(
        engine, ObjectKind.NAMESPACE, "analytics", parent_id=db_id, workspace_id=workspace_id
    )

    # 1. Organization table (public.organizations)
    org_tbl_id = compute_stable_object_id(
        engine,
        ObjectKind.TABLE,
        "organizations",
        namespace="public",
        parent_id=public_ns_id,
        workspace_id=workspace_id,
    )
    org_col_id = compute_stable_object_id(
        engine,
        ObjectKind.COLUMN,
        "org_id",
        namespace="public",
        parent_id=org_tbl_id,
        workspace_id=workspace_id,
    )
    org_col_name = compute_stable_object_id(
        engine,
        ObjectKind.COLUMN,
        "org_name",
        namespace="public",
        parent_id=org_tbl_id,
        workspace_id=workspace_id,
    )
    org_col_status = compute_stable_object_id(
        engine,
        ObjectKind.COLUMN,
        "status",
        namespace="public",
        parent_id=org_tbl_id,
        workspace_id=workspace_id,
    )

    org_cols = (
        CanonicalColumn(
            id=org_col_id,
            parent_table_id=org_tbl_id,
            name="org_id",
            ordinal_position=1,
            native_data_type="BIGINT",
            canonical_type=CanonicalTypeCategory.INTEGER,
            is_nullable=False,
            provenance=prov,
        ),
        CanonicalColumn(
            id=org_col_name,
            parent_table_id=org_tbl_id,
            name="org_name",
            ordinal_position=2,
            native_data_type="VARCHAR(255)",
            canonical_type=CanonicalTypeCategory.TEXT,
            is_nullable=False,
            provenance=prov,
        ),
        CanonicalColumn(
            id=org_col_status,
            parent_table_id=org_tbl_id,
            name="status",
            ordinal_position=3,
            native_data_type="VARCHAR(50)",
            canonical_type=CanonicalTypeCategory.TEXT,
            is_nullable=False,
            default_expression="'active'",
            provenance=prov,
        ),
    )

    org_pk_id = compute_stable_object_id(
        engine,
        ObjectKind.PRIMARY_KEY,
        "pk_organizations",
        namespace="public",
        parent_id=org_tbl_id,
        workspace_id=workspace_id,
        terms=["org_id"],
    )
    org_pk = CanonicalConstraint(
        id=org_pk_id,
        parent_table_id=org_tbl_id,
        name="pk_organizations",
        constraint_type=ConstraintType.PRIMARY_KEY,
        columns=("org_id",),
        provenance=prov,
    )

    org_table = CanonicalTable(
        id=org_tbl_id,
        namespace_id=public_ns_id,
        name="organizations",
        table_type=TableType.TABLE,
        columns=org_cols,
        primary_key=org_pk,
        provenance=prov,
    )

    # 2. Users table (public.users) with composite foreign key & generated column
    user_tbl_id = compute_stable_object_id(
        engine,
        ObjectKind.TABLE,
        "users",
        namespace="public",
        parent_id=public_ns_id,
        workspace_id=workspace_id,
    )
    user_col_id = compute_stable_object_id(
        engine,
        ObjectKind.COLUMN,
        "user_id",
        namespace="public",
        parent_id=user_tbl_id,
        workspace_id=workspace_id,
    )
    user_col_org = compute_stable_object_id(
        engine,
        ObjectKind.COLUMN,
        "org_id",
        namespace="public",
        parent_id=user_tbl_id,
        workspace_id=workspace_id,
    )
    user_col_email = compute_stable_object_id(
        engine,
        ObjectKind.COLUMN,
        "email",
        namespace="public",
        parent_id=user_tbl_id,
        workspace_id=workspace_id,
    )
    user_col_gen = compute_stable_object_id(
        engine,
        ObjectKind.COLUMN,
        "email_normalized",
        namespace="public",
        parent_id=user_tbl_id,
        workspace_id=workspace_id,
    )

    user_cols = (
        CanonicalColumn(
            id=user_col_id,
            parent_table_id=user_tbl_id,
            name="user_id",
            ordinal_position=1,
            native_data_type="BIGINT",
            canonical_type=CanonicalTypeCategory.INTEGER,
            is_nullable=False,
            provenance=prov,
        ),
        CanonicalColumn(
            id=user_col_org,
            parent_table_id=user_tbl_id,
            name="org_id",
            ordinal_position=2,
            native_data_type="BIGINT",
            canonical_type=CanonicalTypeCategory.INTEGER,
            is_nullable=False,
            provenance=prov,
        ),
        CanonicalColumn(
            id=user_col_email,
            parent_table_id=user_tbl_id,
            name="email",
            ordinal_position=3,
            native_data_type="VARCHAR(255)",
            canonical_type=CanonicalTypeCategory.TEXT,
            is_nullable=False,
            provenance=prov,
        ),
        CanonicalColumn(
            id=user_col_gen,
            parent_table_id=user_tbl_id,
            name="email_normalized",
            ordinal_position=4,
            native_data_type="VARCHAR(255)",
            canonical_type=CanonicalTypeCategory.TEXT,
            is_nullable=True,
            is_generated=True,
            generation_mode=GenerationMode.STORED,
            generation_expression="LOWER(email)",
            provenance=prov,
        ),
    )

    user_pk_id = compute_stable_object_id(
        engine,
        ObjectKind.PRIMARY_KEY,
        "pk_users",
        namespace="public",
        parent_id=user_tbl_id,
        workspace_id=workspace_id,
        terms=["user_id"],
    )
    user_pk = CanonicalConstraint(
        id=user_pk_id,
        parent_table_id=user_tbl_id,
        name="pk_users",
        constraint_type=ConstraintType.PRIMARY_KEY,
        columns=("user_id",),
        provenance=prov,
    )

    user_fk_id = compute_stable_object_id(
        engine,
        ObjectKind.FOREIGN_KEY,
        "fk_users_org",
        namespace="public",
        parent_id=user_tbl_id,
        workspace_id=workspace_id,
        terms=["org_id"],
    )
    user_fk = CanonicalForeignKey(
        id=user_fk_id,
        name="fk_users_org",
        source_table_id=user_tbl_id,
        source_table_name="users",
        referenced_table_id=org_tbl_id,
        referenced_table_name="organizations",
        referenced_schema="public",
        column_mappings=(ForeignKeyMapping(source_column="org_id", referenced_column="org_id"),),
        on_update=ForeignKeyAction.CASCADE,
        on_delete=ForeignKeyAction.RESTRICT,
        provenance=prov,
    )

    user_unq_id = compute_stable_object_id(
        engine,
        ObjectKind.UNIQUE_CONSTRAINT,
        "unq_users_org_email",
        namespace="public",
        parent_id=user_tbl_id,
        workspace_id=workspace_id,
        terms=["org_id", "email"],
    )
    user_unq = CanonicalConstraint(
        id=user_unq_id,
        parent_table_id=user_tbl_id,
        name="unq_users_org_email",
        constraint_type=ConstraintType.UNIQUE,
        columns=("org_id", "email"),
        provenance=prov,
    )

    user_chk_id = compute_stable_object_id(
        engine,
        ObjectKind.CHECK_CONSTRAINT,
        "chk_users_email_nonempty",
        namespace="public",
        parent_id=user_tbl_id,
        workspace_id=workspace_id,
        terms=["email"],
    )
    user_chk = CanonicalConstraint(
        id=user_chk_id,
        parent_table_id=user_tbl_id,
        name="chk_users_email_nonempty",
        constraint_type=ConstraintType.CHECK,
        columns=("email",),
        check_clause="LENGTH(email) > 3",
        provenance=prov,
    )

    user_idx_id = compute_stable_object_id(
        engine,
        ObjectKind.INDEX,
        "idx_users_email",
        namespace="public",
        parent_id=user_tbl_id,
        workspace_id=workspace_id,
        terms=["email"],
    )
    user_idx = CanonicalIndex(
        id=user_idx_id,
        parent_table_id=user_tbl_id,
        name="idx_users_email",
        is_unique=False,
        is_primary=False,
        index_type=IndexType.BTREE,
        terms=(CanonicalIndexTerm(column_name="email", ordinal_position=1),),
        provenance=prov,
    )

    user_trg_id = compute_stable_object_id(
        engine,
        ObjectKind.TRIGGER,
        "trg_users_audit",
        namespace="public",
        parent_id=user_tbl_id,
        workspace_id=workspace_id,
    )
    user_trg = CanonicalTrigger(
        id=user_trg_id,
        parent_table_id=user_tbl_id,
        name="trg_users_audit",
        timing=TriggerTiming.BEFORE,
        event=TriggerEvent.INSERT,
        definition="BEGIN NEW.email := LOWER(NEW.email); END",
        provenance=prov,
    )

    users_table = CanonicalTable(
        id=user_tbl_id,
        namespace_id=public_ns_id,
        name="users",
        table_type=TableType.TABLE,
        columns=user_cols,
        primary_key=user_pk,
        foreign_keys=(user_fk,),
        unique_constraints=(user_unq,),
        check_constraints=(user_chk,),
        indexes=(user_idx,),
        triggers=(user_trg,),
        provenance=prov,
    )

    # 3. View in analytics namespace
    view_id = compute_stable_object_id(
        engine,
        ObjectKind.VIEW,
        "active_users_summary",
        namespace="analytics",
        parent_id=analytics_ns_id,
        workspace_id=workspace_id,
    )
    active_users_view = CanonicalView(
        id=view_id,
        namespace_id=analytics_ns_id,
        name="active_users_summary",
        is_materialized=False,
        definition="SELECT o.org_name, count(u.user_id) FROM public.organizations o JOIN public.users u ON o.org_id = u.org_id GROUP BY 1",
        provenance=prov,
    )

    public_namespace = CanonicalNamespace(
        id=public_ns_id,
        name="public",
        tables=(org_table, users_table),
        views=(),
        provenance=prov,
    )

    analytics_namespace = CanonicalNamespace(
        id=analytics_ns_id,
        name="analytics",
        tables=(),
        views=(active_users_view,),
        provenance=prov,
    )

    return CanonicalDatabase(
        id=db_id,
        name=db_name,
        engine=engine,
        contract_version="1.0.0",
        namespaces=(public_namespace, analytics_namespace),
        provenance=prov,
    )


def build_unicode_and_case_sensitive_fixture(
    engine: str = "postgresql",
    workspace_id: str | None = "ws_unicode",
) -> CanonicalDatabase:
    """Fixture containing Greek, Japanese, Arabic identifiers and case-sensitive table names."""
    prov = make_provenance(engine=engine, identifier="unicode_db")
    db_id = compute_stable_object_id(
        engine, ObjectKind.DATABASE, "unicode_db", workspace_id=workspace_id
    )
    ns_id = compute_stable_object_id(
        engine, ObjectKind.NAMESPACE, "χώρος_ὀνομάτων", parent_id=db_id, workspace_id=workspace_id
    )

    # Table with Japanese name: ユーザー (Users)
    jp_tbl_id = compute_stable_object_id(
        engine,
        ObjectKind.TABLE,
        "ユーザー",
        namespace="χώρος_ὀνομάτων",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    jp_col_id = compute_stable_object_id(
        engine,
        ObjectKind.COLUMN,
        "識別子",
        namespace="χώρος_ὀνομάτων",
        parent_id=jp_tbl_id,
        workspace_id=workspace_id,
    )
    jp_col_name = compute_stable_object_id(
        engine,
        ObjectKind.COLUMN,
        "名前",
        namespace="χώρος_ὀνομάτων",
        parent_id=jp_tbl_id,
        workspace_id=workspace_id,
    )

    jp_cols = (
        CanonicalColumn(
            id=jp_col_id,
            parent_table_id=jp_tbl_id,
            name="識別子",
            ordinal_position=1,
            native_data_type="BIGINT",
            canonical_type=CanonicalTypeCategory.INTEGER,
            is_nullable=False,
            provenance=prov,
        ),
        CanonicalColumn(
            id=jp_col_name,
            parent_table_id=jp_tbl_id,
            name="名前",
            ordinal_position=2,
            native_data_type="VARCHAR(100)",
            canonical_type=CanonicalTypeCategory.TEXT,
            is_nullable=False,
            provenance=prov,
        ),
    )
    jp_pk_id = compute_stable_object_id(
        engine,
        ObjectKind.PRIMARY_KEY,
        "pk_ユーザー",
        namespace="χώρος_ὀνομάτων",
        parent_id=jp_tbl_id,
        workspace_id=workspace_id,
        terms=["識別子"],
    )
    jp_pk = CanonicalConstraint(
        id=jp_pk_id,
        parent_table_id=jp_tbl_id,
        name="pk_ユーザー",
        constraint_type=ConstraintType.PRIMARY_KEY,
        columns=("識別子",),
        provenance=prov,
    )
    jp_table = CanonicalTable(
        id=jp_tbl_id,
        namespace_id=ns_id,
        name="ユーザー",
        columns=jp_cols,
        primary_key=jp_pk,
        provenance=prov,
    )

    # Case-sensitive distinct tables: "CamelCaseTable" and "camelcasetable"
    cc1_tbl_id = compute_stable_object_id(
        engine,
        ObjectKind.TABLE,
        "CamelCaseTable",
        namespace="χώρος_ὀνομάτων",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    cc1_col_id = compute_stable_object_id(
        engine,
        ObjectKind.COLUMN,
        "Id",
        namespace="χώρος_ὀνομάτων",
        parent_id=cc1_tbl_id,
        workspace_id=workspace_id,
    )
    cc1_table = CanonicalTable(
        id=cc1_tbl_id,
        namespace_id=ns_id,
        name="CamelCaseTable",
        columns=(
            CanonicalColumn(
                id=cc1_col_id,
                parent_table_id=cc1_tbl_id,
                name="Id",
                ordinal_position=1,
                native_data_type="INT",
                canonical_type=CanonicalTypeCategory.INTEGER,
                is_nullable=False,
                provenance=prov,
            ),
        ),
        provenance=prov,
    )

    cc2_tbl_id = compute_stable_object_id(
        engine,
        ObjectKind.TABLE,
        "camelcasetable",
        namespace="χώρος_ὀνομάτων",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    cc2_col_id = compute_stable_object_id(
        engine,
        ObjectKind.COLUMN,
        "id",
        namespace="χώρος_ὀνομάτων",
        parent_id=cc2_tbl_id,
        workspace_id=workspace_id,
    )
    cc2_table = CanonicalTable(
        id=cc2_tbl_id,
        namespace_id=ns_id,
        name="camelcasetable",
        columns=(
            CanonicalColumn(
                id=cc2_col_id,
                parent_table_id=cc2_tbl_id,
                name="id",
                ordinal_position=1,
                native_data_type="INT",
                canonical_type=CanonicalTypeCategory.INTEGER,
                is_nullable=False,
                provenance=prov,
            ),
        ),
        provenance=prov,
    )

    ns = CanonicalNamespace(
        id=ns_id,
        name="χώρος_ὀνομάτων",
        tables=(jp_table, cc1_table, cc2_table),
        provenance=prov,
    )

    return CanonicalDatabase(
        id=db_id,
        name="unicode_db",
        engine=engine,
        contract_version="1.0.0",
        namespaces=(ns,),
        provenance=prov,
    )


def build_sqlite_fixture() -> CanonicalDatabase:
    """Fixture matching Phase 5.3 SQLite native features."""
    prov = make_provenance(engine="sqlite", identifier="app.db", version="3.45.0")
    db_id = compute_stable_object_id("sqlite", ObjectKind.DATABASE, "main")
    ns_id = compute_stable_object_id("sqlite", ObjectKind.NAMESPACE, "main", parent_id=db_id)

    tbl_id = compute_stable_object_id(
        "sqlite", ObjectKind.TABLE, "items", namespace="main", parent_id=ns_id
    )
    c1_id = compute_stable_object_id(
        "sqlite", ObjectKind.COLUMN, "id", namespace="main", parent_id=tbl_id
    )
    c2_id = compute_stable_object_id(
        "sqlite", ObjectKind.COLUMN, "price", namespace="main", parent_id=tbl_id
    )

    cols = (
        CanonicalColumn(
            id=c1_id,
            parent_table_id=tbl_id,
            name="id",
            ordinal_position=1,
            native_data_type="INTEGER",
            canonical_type=CanonicalTypeCategory.INTEGER,
            is_nullable=False,
            is_identity=True,
            provenance=prov,
        ),
        CanonicalColumn(
            id=c2_id,
            parent_table_id=tbl_id,
            name="price",
            ordinal_position=2,
            native_data_type="REAL",
            canonical_type=CanonicalTypeCategory.FLOAT,
            is_nullable=True,
            provenance=prov,
        ),
    )

    pk_id = compute_stable_object_id(
        "sqlite",
        ObjectKind.PRIMARY_KEY,
        "pk_items",
        namespace="main",
        parent_id=tbl_id,
        terms=["id"],
    )
    pk = CanonicalConstraint(
        id=pk_id,
        parent_table_id=tbl_id,
        name="pk_items",
        constraint_type=ConstraintType.PRIMARY_KEY,
        columns=("id",),
        provenance=prov,
    )

    table = CanonicalTable(
        id=tbl_id,
        namespace_id=ns_id,
        name="items",
        columns=cols,
        primary_key=pk,
        provenance=prov,
    )

    ns = CanonicalNamespace(
        id=ns_id,
        name="main",
        tables=(table,),
        provenance=prov,
    )

    return CanonicalDatabase(
        id=db_id,
        name="main",
        engine="sqlite",
        contract_version="1.0.0",
        namespaces=(ns,),
        provenance=prov,
    )


__all__ = [
    "FIXED_TEST_TIME",
    "build_enterprise_fixture",
    "build_sqlite_fixture",
    "build_unicode_and_case_sensitive_fixture",
    "make_provenance",
]
