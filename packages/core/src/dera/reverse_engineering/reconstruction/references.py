"""Reference resolution engine for Phase 6.2 Structural Reconstruction.

Resolves foreign key references against the Phase 6.1 ObjectRegistry without
fabricating targets or inferring relationships from naming conventions.
"""

from collections.abc import Sequence

from dera.metadata.identity import ObjectId
from dera.metadata.models import CanonicalTable
from dera.reverse_engineering.reconstruction.models import (
    ReconstructedForeignKey,
    ReconstructedTable,
)
from dera.reverse_engineering.references import ResolutionStatus
from dera.reverse_engineering.registry import ObjectRegistry


def resolve_foreign_key_reference(
    fk: ReconstructedForeignKey,
    registry: ObjectRegistry,
    available_tables: dict[tuple[str, str], ReconstructedTable] | None = None,
) -> ReconstructedForeignKey:
    """Resolve a foreign key's target table and column references against the registry."""
    if fk.resolution_status == ResolutionStatus.RESOLVED and fk.referenced_table_id:
        return fk

    target_id = fk.referenced_table_id
    target_table: CanonicalTable | None = None

    if target_id is not None:
        target_table = registry.get_typed(target_id, CanonicalTable)

    # If target_id not found or not set, look up by namespace & table name
    if target_table is None and fk.referenced_table_name:
        if available_tables:
            ns_key = fk.referenced_namespace or ""
            reconstructed_target = available_tables.get((ns_key, fk.referenced_table_name))
            if reconstructed_target:
                target_id = reconstructed_target.object_id

        if target_id is None:
            # Query registry
            for candidate in registry.get_by_kind("table"):
                if isinstance(candidate, CanonicalTable):
                    if candidate.name == fk.referenced_table_name:
                        tbl_schema = getattr(candidate, "schema_name", None)
                        if (
                            not tbl_schema
                            and hasattr(candidate, "namespace_id")
                            and registry.contains(candidate.namespace_id)
                        ):
                            tbl_schema = registry.get_namespace(candidate.namespace_id).name
                        if (
                            fk.referenced_namespace is None
                            or tbl_schema == fk.referenced_namespace
                        ):
                            target_table = candidate
                            target_id = candidate.id
                            break

    if target_table is None and target_id is not None:
        target_table = registry.get_typed(target_id, CanonicalTable)

    # Determine resolution status and column IDs
    if target_table is None:
        new_status = ResolutionStatus.MISSING
        resolved_col_ids = fk.referenced_column_ids
    else:
        new_status = ResolutionStatus.RESOLVED
        resolved_col_ids_list: list[ObjectId] = []
        target_cols_by_name = {col.name: col.id for col in target_table.columns}

        for ref_col_name in fk.referenced_column_names:
            cid = target_cols_by_name.get(ref_col_name)
            if cid is None:
                new_status = ResolutionStatus.INVALID
                break
            resolved_col_ids_list.append(cid)

        resolved_col_ids = (
            tuple(resolved_col_ids_list)
            if new_status == ResolutionStatus.RESOLVED
            else fk.referenced_column_ids
        )

    return fk.model_copy(
        update={
            "referenced_table_id": target_id,
            "referenced_column_ids": resolved_col_ids,
            "resolution_status": new_status,
        }
    )


def resolve_all_references(
    tables: Sequence[ReconstructedTable],
    registry: ObjectRegistry,
) -> tuple[ReconstructedTable, ...]:
    """Resolve all foreign key references across all reconstructed tables."""
    table_map = {(t.namespace, t.native_name): t for t in tables}
    resolved_tables: list[ReconstructedTable] = []

    for tbl in tables:
        updated_fks = tuple(
            resolve_foreign_key_reference(fk, registry, table_map) for fk in tbl.foreign_keys
        )
        resolved_tables.append(tbl.model_copy(update={"foreign_keys": updated_fks}))

    return tuple(resolved_tables)
