"""Test fixtures and generators for Phase 6.5 Schema Snapshots & Deterministic Fingerprints.

Provides canonical test database fixtures across engines and topologies:
- Empty database
- Single-table schema
- Multi-namespace schema
- Composite PK/FK constraints
- Complex dependencies and cycles
- Unicode and case-sensitive identifiers
- Engines: PostgreSQL, SQLite, MySQL, MariaDB
"""

from __future__ import annotations

from datetime import UTC, datetime

from dera.metadata.enums import (
    CanonicalTypeCategory,
    ForeignKeyAction,
    MetadataCompleteness,
    ObjectKind,
)
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.models import (
    CanonicalColumn,
    CanonicalConstraint,
    CanonicalDatabase,
    CanonicalForeignKey,
    CanonicalIndex,
    CanonicalIndexTerm,
    CanonicalNamespace,
    CanonicalTable,
)
from dera.metadata.provenance import MetadataProvenance
from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.dependencies.analyzer import DependencyAnalyzer
from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.reconstruction.builder import StructuralReconstructionBuilder
from dera.reverse_engineering.reconstruction.models import StructuralReconstructionResult
from dera.reverse_engineering.schema import SchemaRepresentation
from dera.reverse_engineering.snapshots.builder import SchemaSnapshotBuilder
from dera.reverse_engineering.snapshots.models import SchemaSnapshot


def make_test_provenance(
    engine: str = "postgresql",
    identifier: str = "test_src",
    completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE,
) -> MetadataProvenance:
    """Create deterministic provenance for snapshot tests."""
    return MetadataProvenance(
        source_engine=engine,
        source_version="16.0" if "postgres" in engine else "3.42.0",
        connector_version="1.0.0",
        collection_timestamp=datetime(2026, 10, 28, 12, 0, 0, tzinfo=UTC),
        completeness=completeness,
        native_identifier=identifier,
    )


def make_col(
    table_id: str,
    name: str,
    ordinal: int,
    data_type: str = "integer",
    canonical_type: CanonicalTypeCategory = CanonicalTypeCategory.INTEGER,
    is_nullable: bool = False,
    engine: str = "postgresql",
    workspace_id: str = "ws_test",
) -> CanonicalColumn:
    """Helper to build a deterministic CanonicalColumn."""
    cid = compute_stable_object_id(
        kind=ObjectKind.COLUMN,
        engine=engine,
        parent_id=table_id,
        native_name=name,
        workspace_id=workspace_id,
    )
    return CanonicalColumn(
        id=cid,
        table_id=table_id,
        name=name,
        ordinal_position=ordinal,
        native_type=data_type,
        canonical_type=canonical_type,
        is_nullable=is_nullable,
        provenance=make_test_provenance(engine=engine, identifier=name),
    )


def make_empty_database(
    name: str = "empty_db",
    engine: str = "postgresql",
    workspace_id: str = "ws_test",
) -> CanonicalDatabase:
    """Construct a database with zero tables."""
    db_id = compute_stable_object_id(
        kind=ObjectKind.DATABASE,
        engine=engine,
        parent_id="",
        native_name=name,
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        kind=ObjectKind.NAMESPACE,
        engine=engine,
        parent_id=db_id,
        native_name="public",
        workspace_id=workspace_id,
    )
    return CanonicalDatabase(
        id=db_id,
        name=name,
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=(),
                provenance=make_test_provenance(engine=engine),
            ),
        ),
        provenance=make_test_provenance(engine=engine),
    )


def make_single_table_database(
    name: str = "single_tbl_db",
    engine: str = "postgresql",
    workspace_id: str = "ws_test",
) -> CanonicalDatabase:
    """Construct a database with a single users table."""
    db_id = compute_stable_object_id(
        kind=ObjectKind.DATABASE,
        engine=engine,
        parent_id="",
        native_name=name,
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        kind=ObjectKind.NAMESPACE,
        engine=engine,
        parent_id=db_id,
        native_name="public",
        workspace_id=workspace_id,
    )
    tbl_id = compute_stable_object_id(
        kind=ObjectKind.TABLE,
        engine=engine,
        parent_id=ns_id,
        native_name="users",
        workspace_id=workspace_id,
    )
    pk_id = compute_stable_object_id(
        kind=ObjectKind.PRIMARY_KEY,
        engine=engine,
        parent_id=tbl_id,
        native_name="pk_users",
        workspace_id=workspace_id,
    )
    idx_id = compute_stable_object_id(
        kind=ObjectKind.INDEX,
        engine=engine,
        parent_id=tbl_id,
        native_name="idx_users_email",
        workspace_id=workspace_id,
    )

    tbl = CanonicalTable(
        id=tbl_id,
        namespace_id=ns_id,
        name="users",
        schema_name="public",
        columns=(
            make_col(
                tbl_id,
                "id",
                1,
                "integer",
                CanonicalTypeCategory.INTEGER,
                False,
                engine,
                workspace_id,
            ),
            make_col(
                tbl_id,
                "email",
                2,
                "varchar",
                CanonicalTypeCategory.TEXT,
                False,
                engine,
                workspace_id,
            ),
            make_col(
                tbl_id, "name", 3, "varchar", CanonicalTypeCategory.TEXT, True, engine, workspace_id
            ),
        ),
        primary_key=CanonicalConstraint(
            id=pk_id,
            table_id=tbl_id,
            name="pk_users",
            constraint_type="PRIMARY_KEY",
            columns=("id",),
            provenance=make_test_provenance(engine=engine),
        ),
        indexes=(
            CanonicalIndex(
                id=idx_id,
                parent_table_id=tbl_id,
                name="idx_users_email",
                terms=(
                    CanonicalIndexTerm(
                        column_name="email",
                        ordinal_position=1,
                    ),
                ),
                is_unique=True,
                provenance=make_test_provenance(engine=engine),
            ),
        ),
        provenance=make_test_provenance(engine=engine),
    )

    return CanonicalDatabase(
        id=db_id,
        name=name,
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=(tbl,),
                provenance=make_test_provenance(engine=engine),
            ),
        ),
        provenance=make_test_provenance(engine=engine),
    )


def make_composite_constraints_database(
    name: str = "composite_db",
    engine: str = "postgresql",
    workspace_id: str = "ws_test",
) -> CanonicalDatabase:
    """Construct a database with composite primary key and composite foreign key."""
    db_id = compute_stable_object_id(
        kind=ObjectKind.DATABASE,
        engine=engine,
        parent_id="",
        native_name=name,
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        kind=ObjectKind.NAMESPACE,
        engine=engine,
        parent_id=db_id,
        native_name="public",
        workspace_id=workspace_id,
    )
    parent_id = compute_stable_object_id(
        kind=ObjectKind.TABLE,
        engine=engine,
        parent_id=ns_id,
        native_name="parent_items",
        workspace_id=workspace_id,
    )
    child_id = compute_stable_object_id(
        kind=ObjectKind.TABLE,
        engine=engine,
        parent_id=ns_id,
        native_name="child_items",
        workspace_id=workspace_id,
    )

    pk_parent = CanonicalConstraint(
        id=compute_stable_object_id(
            kind=ObjectKind.PRIMARY_KEY,
            engine=engine,
            parent_id=parent_id,
            native_name="pk_parent",
            workspace_id=workspace_id,
        ),
        table_id=parent_id,
        name="pk_parent",
        constraint_type="PRIMARY_KEY",
        columns=("tenant_id", "item_id"),  # Composite PK
        provenance=make_test_provenance(engine=engine),
    )

    parent_tbl = CanonicalTable(
        id=parent_id,
        namespace_id=ns_id,
        name="parent_items",
        schema_name="public",
        columns=(
            make_col(
                parent_id,
                "tenant_id",
                1,
                "integer",
                CanonicalTypeCategory.INTEGER,
                False,
                engine,
                workspace_id,
            ),
            make_col(
                parent_id,
                "item_id",
                2,
                "integer",
                CanonicalTypeCategory.INTEGER,
                False,
                engine,
                workspace_id,
            ),
            make_col(
                parent_id,
                "label",
                3,
                "varchar",
                CanonicalTypeCategory.TEXT,
                True,
                engine,
                workspace_id,
            ),
        ),
        primary_key=pk_parent,
        provenance=make_test_provenance(engine=engine),
    )

    fk_child = CanonicalForeignKey(
        id=compute_stable_object_id(
            kind=ObjectKind.FOREIGN_KEY,
            engine=engine,
            parent_id=child_id,
            native_name="fk_child_parent",
            workspace_id=workspace_id,
        ),
        table_id=child_id,
        name="fk_child_parent",
        column_names=("t_id", "it_id"),  # Composite FK
        referenced_table_id=parent_id,
        referenced_schema_name="public",
        referenced_table_name="parent_items",
        referenced_column_names=("tenant_id", "item_id"),
        on_update=ForeignKeyAction.CASCADE,
        on_delete=ForeignKeyAction.RESTRICT,
        provenance=make_test_provenance(engine=engine),
    )

    child_tbl = CanonicalTable(
        id=child_id,
        namespace_id=ns_id,
        name="child_items",
        schema_name="public",
        columns=(
            make_col(
                child_id,
                "id",
                1,
                "integer",
                CanonicalTypeCategory.INTEGER,
                False,
                engine,
                workspace_id,
            ),
            make_col(
                child_id,
                "t_id",
                2,
                "integer",
                CanonicalTypeCategory.INTEGER,
                False,
                engine,
                workspace_id,
            ),
            make_col(
                child_id,
                "it_id",
                3,
                "integer",
                CanonicalTypeCategory.INTEGER,
                False,
                engine,
                workspace_id,
            ),
        ),
        foreign_keys=(fk_child,),
        provenance=make_test_provenance(engine=engine),
    )

    return CanonicalDatabase(
        id=db_id,
        name=name,
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=(parent_tbl, child_tbl),
                provenance=make_test_provenance(engine=engine),
            ),
        ),
        provenance=make_test_provenance(engine=engine),
    )


def make_unicode_database(
    name: str = "unicode_db",
    engine: str = "postgresql",
    workspace_id: str = "ws_test",
) -> CanonicalDatabase:
    """Construct a database with non-ASCII Unicode identifiers and accented characters."""
    db_id = compute_stable_object_id(
        kind=ObjectKind.DATABASE,
        engine=engine,
        parent_id="",
        native_name=name,
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        kind=ObjectKind.NAMESPACE,
        engine=engine,
        parent_id=db_id,
        native_name="public",
        workspace_id=workspace_id,
    )
    tbl_id = compute_stable_object_id(
        kind=ObjectKind.TABLE,
        engine=engine,
        parent_id=ns_id,
        native_name="café_données",
        workspace_id=workspace_id,
    )

    tbl = CanonicalTable(
        id=tbl_id,
        namespace_id=ns_id,
        name="café_données",
        schema_name="public",
        columns=(
            make_col(
                tbl_id,
                "identifiant",
                1,
                "integer",
                CanonicalTypeCategory.INTEGER,
                False,
                engine,
                workspace_id,
            ),
            make_col(
                tbl_id,
                "libellé_français",
                2,
                "varchar",
                CanonicalTypeCategory.TEXT,
                False,
                engine,
                workspace_id,
            ),
            make_col(
                tbl_id,
                "valeur_€",
                3,
                "numeric",
                CanonicalTypeCategory.DECIMAL,
                True,
                engine,
                workspace_id,
            ),
        ),
        provenance=make_test_provenance(engine=engine),
    )

    return CanonicalDatabase(
        id=db_id,
        name=name,
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=(tbl,),
                provenance=make_test_provenance(engine=engine),
            ),
        ),
        provenance=make_test_provenance(engine=engine),
    )


def build_full_analysis(
    db: CanonicalDatabase,
) -> tuple[
    SchemaRepresentation,
    StructuralReconstructionResult,
    ForeignKeyGraph,
    DependencyAnalysisResult,
]:
    """Run full reverse engineering pipeline across Phases 6.1 through 6.4."""
    schema = SchemaBuilder.from_canonical_database(db)
    recon = StructuralReconstructionBuilder().build_from_schema(schema)
    graph = ForeignKeyGraphBuilder.from_schema(schema)
    dep = DependencyAnalyzer().analyze(graph, schema=schema)
    return schema, recon, graph, dep


def build_snapshot_from_database(
    db: CanonicalDatabase,
    workspace_id: str = "ws_test",
    snapshot_id: str | None = None,
    tags: dict[str, str] | None = None,
) -> SchemaSnapshot:
    """Convenience helper to build a full SchemaSnapshot from a CanonicalDatabase."""
    schema, recon, graph, dep = build_full_analysis(db)
    return SchemaSnapshotBuilder.from_analysis(
        schema=schema,
        reconstruction=recon,
        relationships=graph,
        dependencies=dep,
        workspace_id=workspace_id,
        snapshot_id=snapshot_id,
        tags=tags,
    )
