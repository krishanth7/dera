"""DERA Reverse Engineering — Phase 6.5 Snapshot Canonicalization.

Transforms reverse engineering artifacts (SchemaRepresentation, StructuralReconstructionResult,
ForeignKeyGraph, DependencyAnalysisResult) into canonical, strictly ordered,
immutable SnapshotStructuralPayload structures.

Guarantees:
- Strict lexicographical ordering for namespaces, tables, views, triggers, and constraints.
- Semantic ordinal position preserved for table columns.
- Composite key column sequences preserved exactly as declared in the source schema.
- Volatile operational metadata (timestamps, request IDs, workspace IDs) strictly excluded.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.metadata.enums import (
    TableType,
)
from dera.reverse_engineering.snapshots.models import (
    SnapshotCheckConstraintPayload,
    SnapshotColumnPayload,
    SnapshotDependencySummary,
    SnapshotForeignKeyPayload,
    SnapshotIndexPayload,
    SnapshotPrimaryKeyPayload,
    SnapshotRelationshipPayload,
    SnapshotStructuralPayload,
    SnapshotTablePayload,
    SnapshotTriggerPayload,
    SnapshotUniqueConstraintPayload,
    SnapshotViewPayload,
)

if TYPE_CHECKING:
    from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
    from dera.reverse_engineering.graph.models import ForeignKeyGraph
    from dera.reverse_engineering.reconstruction.models import StructuralReconstructionResult
    from dera.reverse_engineering.schema import SchemaRepresentation


def canonicalize_structural_payload(
    schema: SchemaRepresentation,
    reconstruction: StructuralReconstructionResult | None = None,
    relationships: ForeignKeyGraph | None = None,
    dependencies: DependencyAnalysisResult | None = None,
) -> SnapshotStructuralPayload:
    """Construct a canonical, deterministically sorted SnapshotStructuralPayload from analysis artifacts.

    Args:
        schema: Base SchemaRepresentation from Phase 6.1.
        reconstruction: Optional Phase 6.2 StructuralReconstructionResult with enriched table definitions.
        relationships: Optional Phase 6.3 ForeignKeyGraph.
        dependencies: Optional Phase 6.4 DependencyAnalysisResult.

    Returns:
        Canonical SnapshotStructuralPayload with deterministic ordering.
    """
    # 1. Namespaces
    namespace_names = sorted(ns.name for ns in schema.namespaces)

    # 2. Reconstructed Tables or Fallback to Canonical Tables
    tables_list: list[SnapshotTablePayload] = []

    if reconstruction is not None:
        # Sort reconstructed tables by (namespace, name)
        sorted_reconstructed = sorted(
            reconstruction.tables,
            key=lambda t: (t.namespace, t.native_name),
        )
        canonical_tables_map = {
            (
                t.schema_name if hasattr(t, "schema_name") else getattr(t, "namespace", "public"),
                t.name,
            ): t
            for t in schema.database.all_tables()
        }

        for tbl in sorted_reconstructed:
            # Columns sorted by ordinal_position
            cols = sorted(tbl.columns, key=lambda c: c.ordinal_position)
            col_payloads = tuple(
                SnapshotColumnPayload(
                    column_id=c.object_id,
                    name=c.native_name,
                    ordinal_position=c.ordinal_position,
                    native_data_type=getattr(c, "native_data_type", None)
                    or getattr(c, "native_type", ""),
                    canonical_type=c.canonical_type,
                    is_nullable=(
                        c.nullability.value == "nullable"
                        if hasattr(c.nullability, "value")
                        else bool(c.nullability)
                    ),
                    default_expression=(
                        c.default_value.raw_expression
                        if hasattr(c, "default_value") and c.default_value
                        else getattr(c, "default_expression", None)
                    ),
                    character_maximum_length=getattr(c, "character_maximum_length", None),
                    numeric_precision=getattr(c, "numeric_precision", None),
                    numeric_scale=getattr(c, "numeric_scale", None),
                    comment=c.comment,
                )
                for c in cols
            )

            # Primary Key
            pk_payload: SnapshotPrimaryKeyPayload | None = None
            if tbl.primary_key is not None:
                pk_payload = SnapshotPrimaryKeyPayload(
                    constraint_id=tbl.primary_key.object_id,
                    name=tbl.primary_key.native_name or "PRIMARY",
                    columns=getattr(
                        tbl.primary_key, "column_names", getattr(tbl.primary_key, "columns", ())
                    ),  # Preserves exact composite column order
                )

            # Foreign Keys sorted by name then source_columns
            fks = sorted(
                tbl.foreign_keys,
                key=lambda fk: (
                    fk.native_name or "",
                    getattr(fk, "source_column_names", getattr(fk, "source_columns", ())),
                    getattr(fk, "referenced_table_name", getattr(fk, "referenced_table", "")),
                ),
            )
            fk_payloads = tuple(
                SnapshotForeignKeyPayload(
                    constraint_id=fk.object_id,
                    name=fk.native_name or "FOREIGN_KEY",
                    source_columns=getattr(
                        fk, "source_column_names", getattr(fk, "source_columns", ())
                    ),
                    target_namespace=fk.referenced_namespace or tbl.namespace,
                    target_table=getattr(
                        fk, "referenced_table_name", getattr(fk, "referenced_table", "")
                    ),
                    target_columns=getattr(
                        fk, "referenced_column_names", getattr(fk, "referenced_columns", ())
                    ),
                    on_update=fk.on_update,
                    on_delete=fk.on_delete,
                    is_deferrable=getattr(fk, "deferrability", None) is not None
                    and "DEFER" in str(fk.deferrability).upper(),
                    initially_deferred=getattr(fk, "deferrability", None) is not None
                    and "INITIALLY DEFERRED" in str(fk.deferrability).upper(),
                )
                for fk in fks
            )

            # Unique constraints sorted by name then columns
            uqs = sorted(
                tbl.unique_constraints,
                key=lambda uq: (
                    uq.native_name or "",
                    getattr(uq, "column_names", getattr(uq, "columns", ())),
                ),
            )
            uq_payloads = tuple(
                SnapshotUniqueConstraintPayload(
                    constraint_id=uq.object_id,
                    name=uq.native_name or "UNIQUE",
                    columns=getattr(uq, "column_names", getattr(uq, "columns", ())),
                )
                for uq in uqs
            )

            # Check constraints sorted by name then expression
            cks = sorted(
                tbl.check_constraints,
                key=lambda ck: (ck.native_name or "", ck.expression),
            )
            ck_payloads = tuple(
                SnapshotCheckConstraintPayload(
                    constraint_id=ck.object_id,
                    name=ck.native_name or "CHECK",
                    expression=ck.expression,
                )
                for ck in cks
            )

            # Indexes from canonical table matching this table if present
            idx_payloads: list[SnapshotIndexPayload] = []
            canonical_tbl = canonical_tables_map.get((tbl.namespace, tbl.native_name))
            if canonical_tbl is not None:
                sorted_indexes = sorted(canonical_tbl.indexes, key=lambda idx: idx.name)
                for idx in sorted_indexes:
                    idx_payloads.append(
                        SnapshotIndexPayload(
                            index_id=getattr(idx, "object_id", None) or idx.id,
                            name=idx.name,
                            columns=getattr(idx, "columns", ()) or getattr(idx, "column_names", ()),
                            is_unique=idx.is_unique,
                            index_type=idx.index_type
                            if isinstance(idx.index_type, str)
                            else idx.index_type.value,
                            predicate=idx.predicate,
                        )
                    )

            tables_list.append(
                SnapshotTablePayload(
                    table_id=tbl.object_id,
                    namespace=tbl.namespace,
                    name=tbl.native_name,
                    table_type=tbl.table_type,
                    columns=col_payloads,
                    primary_key=pk_payload,
                    foreign_keys=fk_payloads,
                    unique_constraints=uq_payloads,
                    check_constraints=ck_payloads,
                    indexes=tuple(idx_payloads),
                    comment=getattr(tbl, "comment", None),
                )
            )
    else:
        # Fallback directly to schema.database.all_tables()
        sorted_canonical_tables = sorted(
            schema.database.all_tables(),
            key=lambda t: (
                t.schema_name if hasattr(t, "schema_name") else getattr(t, "namespace", "public"),
                t.name,
            ),
        )
        for tbl in sorted_canonical_tables:
            tbl_ns = (
                tbl.schema_name
                if hasattr(tbl, "schema_name")
                else getattr(tbl, "namespace", "public")
            )
            tbl_id = getattr(tbl, "object_id", None) or tbl.id
            cols = sorted(tbl.columns, key=lambda c: c.ordinal_position)
            col_payloads = tuple(
                SnapshotColumnPayload(
                    column_id=getattr(c, "object_id", None) or c.id,
                    name=c.name,
                    ordinal_position=c.ordinal_position,
                    native_data_type=getattr(c, "native_data_type", None)
                    or getattr(c, "native_type", "integer"),
                    canonical_type=c.canonical_type,
                    is_nullable=bool(c.is_nullable) if c.is_nullable is not None else True,
                    default_expression=getattr(c, "default_expression", None)
                    or getattr(c, "default_value", None),
                    character_maximum_length=getattr(c, "character_maximum_length", None)
                    or getattr(c, "char_max_length", None),
                    numeric_precision=getattr(c, "numeric_precision", None),
                    numeric_scale=getattr(c, "numeric_scale", None),
                    comment=getattr(c, "comment", None),
                )
                for c in cols
            )

            pk_payload = None
            if tbl.primary_key is not None:
                pk_payload = SnapshotPrimaryKeyPayload(
                    constraint_id=getattr(tbl.primary_key, "object_id", None) or tbl.primary_key.id,
                    name=tbl.primary_key.name,
                    columns=tbl.primary_key.columns,
                )

            fks = sorted(
                tbl.foreign_keys,
                key=lambda fk: (
                    fk.name,
                    fk.column_names if hasattr(fk, "column_names") else fk.source_columns,
                    fk.referenced_table_name
                    if hasattr(fk, "referenced_table_name")
                    else fk.referenced_table,
                ),
            )
            fk_payloads = tuple(
                SnapshotForeignKeyPayload(
                    constraint_id=getattr(fk, "object_id", None) or fk.id,
                    name=fk.name,
                    source_columns=fk.column_names
                    if hasattr(fk, "column_names")
                    else fk.source_columns,
                    target_namespace=getattr(fk, "referenced_schema_name", None)
                    or getattr(fk, "referenced_namespace", None)
                    or tbl_ns,
                    target_table=getattr(fk, "referenced_table_name", None)
                    or getattr(fk, "referenced_table", ""),
                    target_columns=getattr(fk, "referenced_column_names", None)
                    or getattr(fk, "referenced_columns", ()),
                    on_update=fk.on_update,
                    on_delete=fk.on_delete,
                    is_deferrable=getattr(fk, "is_deferrable", False),
                    initially_deferred=getattr(fk, "initially_deferred", False),
                )
                for fk in fks
            )

            uqs = sorted(
                tbl.unique_constraints,
                key=lambda uq: (uq.name, uq.columns),
            )
            uq_payloads = tuple(
                SnapshotUniqueConstraintPayload(
                    constraint_id=getattr(uq, "object_id", None) or uq.id,
                    name=uq.name,
                    columns=uq.columns,
                )
                for uq in uqs
            )

            cks = sorted(
                tbl.check_constraints,
                key=lambda ck: (ck.name, ck.expression),
            )
            ck_payloads = tuple(
                SnapshotCheckConstraintPayload(
                    constraint_id=getattr(ck, "object_id", None) or ck.id,
                    name=ck.name,
                    expression=ck.expression,
                )
                for ck in cks
            )

            idxs = sorted(tbl.indexes, key=lambda idx: idx.name)
            idx_payloads_t = tuple(
                SnapshotIndexPayload(
                    index_id=getattr(idx, "object_id", None) or idx.id,
                    name=idx.name,
                    columns=getattr(idx, "columns", ()) or getattr(idx, "column_names", ()),
                    is_unique=idx.is_unique,
                    index_type=idx.index_type
                    if isinstance(idx.index_type, str)
                    else idx.index_type.value,
                    predicate=idx.predicate,
                )
                for idx in idxs
            )

            raw_tt = getattr(tbl, "table_type", TableType.TABLE)
            table_type_val = (
                raw_tt if isinstance(raw_tt, TableType) else TableType(str(raw_tt).upper())
            )

            tables_list.append(
                SnapshotTablePayload(
                    table_id=tbl_id,
                    namespace=tbl_ns,
                    name=tbl.name,
                    table_type=table_type_val,
                    columns=col_payloads,
                    primary_key=pk_payload,
                    foreign_keys=fk_payloads,
                    unique_constraints=uq_payloads,
                    check_constraints=ck_payloads,
                    indexes=idx_payloads_t,
                    comment=tbl.comment,
                )
            )

    # 3. Views sorted by (namespace, name)
    raw_views = [v for ns in schema.database.namespaces for v in getattr(ns, "views", ())]
    sorted_views = sorted(
        raw_views,
        key=lambda v: (
            v.schema_name if hasattr(v, "schema_name") else getattr(v, "namespace", "public"),
            v.name,
        ),
    )
    view_payloads = tuple(
        SnapshotViewPayload(
            view_id=getattr(v, "object_id", None) or v.id,
            namespace=v.schema_name
            if hasattr(v, "schema_name")
            else getattr(v, "namespace", "public"),
            name=v.name,
            definition=v.definition,
            is_materialized=getattr(v, "is_materialized", False),
        )
        for v in sorted_views
    )

    # 4. Triggers sorted by (namespace, name)
    raw_triggers = [
        tr
        for ns in schema.database.namespaces
        for t in getattr(ns, "tables", ())
        for tr in getattr(t, "triggers", ())
    ]
    sorted_triggers = sorted(
        raw_triggers,
        key=lambda tr: (
            tr.schema_name if hasattr(tr, "schema_name") else getattr(tr, "namespace", "public"),
            tr.name,
        ),
    )
    trigger_payloads = tuple(
        SnapshotTriggerPayload(
            trigger_id=getattr(tr, "object_id", None) or tr.id,
            namespace=tr.schema_name
            if hasattr(tr, "schema_name")
            else getattr(tr, "namespace", "public"),
            name=tr.name,
            table_name=tr.table_name,
            timing=tr.timing if isinstance(tr.timing, str) else tr.timing.value,
            events=tuple(e if isinstance(e, str) else e.value for e in tr.events),
            action_statement=tr.action_statement,
        )
        for tr in sorted_triggers
    )

    # 5. Relationships from ForeignKeyGraph if provided, or from schema foreign key references
    relationship_payloads: list[SnapshotRelationshipPayload] = []
    if relationships is not None:
        sorted_edges = sorted(
            relationships.edges,
            key=lambda e: (
                e.source_table_id,
                getattr(e, "referenced_table_id", None) or getattr(e, "target_table_id", "") or "",
                e.native_name,
            ),
        )
        for edge in sorted_edges:
            ref_tid = (
                getattr(edge, "referenced_table_id", None)
                or getattr(edge, "target_table_id", None)
                or ""
            )
            relationship_payloads.append(
                SnapshotRelationshipPayload(
                    edge_id=getattr(edge, "edge_id", None) or getattr(edge, "object_id", ""),
                    source_table_id=edge.source_table_id,
                    target_table_id=ref_tid,
                    constraint_name=edge.native_name,
                    source_columns=getattr(
                        edge, "source_column_names", getattr(edge, "source_columns", ())
                    ),
                    target_columns=getattr(
                        edge, "referenced_column_names", getattr(edge, "target_columns", ())
                    ),
                )
            )
    else:
        # Fallback to foreign key references in SchemaRepresentation
        sorted_refs = sorted(
            schema.foreign_key_references,
            key=lambda r: (r.source_table_id, r.referenced_table_id or "", r.foreign_key_name),
        )
        for ref in sorted_refs:
            if ref.referenced_table_id is not None:
                relationship_payloads.append(
                    SnapshotRelationshipPayload(
                        edge_id=ref.foreign_key_id,
                        source_table_id=ref.source_table_id,
                        target_table_id=ref.referenced_table_id,
                        constraint_name=ref.foreign_key_name,
                        source_columns=ref.source_columns,
                        target_columns=ref.referenced_columns,
                    )
                )

    # 6. Dependencies Summary
    dep_summary: SnapshotDependencySummary | None = None
    if dependencies is not None:
        dep_summary = SnapshotDependencySummary(
            total_edges=dependencies.edge_count,
            has_cycles=dependencies.cycle_report.has_cycles,
            cycle_count=dependencies.cycle_report.cycle_count,
            scc_count=dependencies.cycle_report.scc_count,
            cyclic_scc_count=dependencies.cycle_report.cyclic_scc_count,
            topological_levels_count=len(dependencies.ordering.levels),
        )

    return SnapshotStructuralPayload(
        schema_format="dera.structural.v1",
        database_name=schema.database_name,
        engine=schema.engine,
        engine_version=schema.engine_version,
        namespaces=tuple(namespace_names),
        tables=tuple(tables_list),
        views=view_payloads,
        triggers=trigger_payloads,
        relationships=tuple(relationship_payloads),
        dependencies=dep_summary,
        completeness=schema.completeness,
    )
