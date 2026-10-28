"""Foreign key reconstruction for Phase 6.2 Structural Reconstruction.

Preserves exact ordered source-to-referenced column pairs for single and composite
foreign keys, resolving targets against the Phase 6.1 ObjectRegistry without
fabricating missing targets.
"""

from collections.abc import Sequence

from dera.metadata.identity import ObjectId
from dera.metadata.models import CanonicalForeignKey, CanonicalTable
from dera.reverse_engineering.reconstruction.errors import (
    ConstraintOwnershipError,
    ForeignKeyReconstructionError,
)
from dera.reverse_engineering.reconstruction.models import (
    ConstraintEnforcementStatus,
    ConstraintValidationStatus,
    ReconstructedColumn,
    ReconstructedForeignKey,
)
from dera.reverse_engineering.references import ResolutionStatus
from dera.reverse_engineering.registry import ObjectRegistry


def reconstruct_foreign_key(
    fk: CanonicalForeignKey,
    source_table_id: ObjectId,
    source_namespace: str,
    columns: Sequence[ReconstructedColumn],
    registry: ObjectRegistry | None = None,
) -> ReconstructedForeignKey:
    """Reconstruct a foreign key constraint and resolve its target reference.

    Preserves source and target column orders strictly.
    """
    col_by_name = {col.native_name: col for col in columns}
    col_by_id = {col.object_id: col for col in columns}

    ordered_src_ids: list[ObjectId] = []
    ordered_src_names: list[str] = []

    # Validate source table ownership
    fk_source = getattr(fk, "source_table_id", None) or getattr(fk, "table_id", None)
    if fk_source and fk_source != source_table_id:
        raise ConstraintOwnershipError(
            f"Foreign key '{fk.name or fk.id}' source table '{fk_source}' does not match owning table '{source_table_id}'."
        )

    src_cols = getattr(fk, "source_columns", None) or getattr(fk, "columns", None)
    if not src_cols and hasattr(fk, "column_mappings"):
        src_cols = tuple(m.source_column for m in fk.column_mappings)

    ref_cols = getattr(fk, "referenced_columns", None)
    if not ref_cols and hasattr(fk, "column_mappings"):
        ref_cols = tuple(m.referenced_column for m in fk.column_mappings)
    if ref_cols is None:
        ref_cols = ()

    ref_table_name = getattr(fk, "referenced_table_name", None) or getattr(fk, "referenced_table", "")

    # Validate source columns belong to source table
    if src_cols:
        for cname in src_cols:
            col = col_by_name.get(cname)
            if col is None:
                raise ConstraintOwnershipError(
                    f"Foreign key '{fk.name or fk.id}' source column '{cname}' does not belong to table '{source_table_id}'."
                )
            ordered_src_names.append(col.native_name)
            ordered_src_ids.append(col.object_id)
    elif getattr(fk, "column_ids", None):
        for cid in fk.column_ids:
            col = col_by_id.get(cid)
            if col is None:
                raise ConstraintOwnershipError(
                    f"Foreign key '{fk.name or fk.id}' source column ObjectId '{cid}' does not belong to table '{source_table_id}'."
                )
            ordered_src_ids.append(col.object_id)
            ordered_src_names.append(col.native_name)
    else:
        raise ForeignKeyReconstructionError(f"Foreign key '{fk.id}' has no source columns.")

    # Validate composite count alignment
    if ref_cols and len(ordered_src_names) != len(ref_cols):
        raise ForeignKeyReconstructionError(
            f"Foreign key '{fk.name or fk.id}' source column count ({len(ordered_src_names)}) does not match "
            f"referenced column count ({len(ref_cols)})."
        )

    # Cross-namespace check
    ref_ns = getattr(fk, "referenced_schema", None) or getattr(fk, "referenced_namespace", None)
    is_cross_ns = ref_ns is not None and ref_ns != source_namespace

    # Target resolution against registry
    resolved_target_id = getattr(fk, "referenced_table_id", None)
    resolved_ref_col_ids: list[ObjectId] = list(getattr(fk, "referenced_column_ids", None) or ())
    resolution_status = ResolutionStatus.MISSING

    if registry is not None:
        target_table: CanonicalTable | None = None
        if resolved_target_id and registry.contains(resolved_target_id):
            target_table = registry.get_table(resolved_target_id)
        elif ref_table_name:
            # Search registry for matching table by namespace & name
            for tbl in registry.get_by_kind("table"):
                if isinstance(tbl, CanonicalTable):
                    tbl_schema = getattr(tbl, "schema_name", None)
                    if (
                        not tbl_schema
                        and hasattr(tbl, "namespace_id")
                        and registry.contains(tbl.namespace_id)
                    ):
                        ns_obj = registry.get_namespace(tbl.namespace_id)
                        tbl_schema = ns_obj.name
                    if tbl.name == ref_table_name and (
                        ref_ns is None or tbl_schema == ref_ns
                    ):
                        target_table = tbl
                        resolved_target_id = tbl.id
                        break

        if target_table is not None:
            # Check referenced columns exist on target
            target_col_names = {c.name: c.id for c in target_table.columns}
            missing_cols = [cname for cname in ref_cols if cname not in target_col_names]
            if missing_cols:
                resolution_status = ResolutionStatus.INVALID
            else:
                resolution_status = ResolutionStatus.RESOLVED
                if not resolved_ref_col_ids and ref_cols:
                    resolved_ref_col_ids = [target_col_names[c] for c in ref_cols]
        else:
            resolution_status = ResolutionStatus.MISSING
    elif resolved_target_id is not None:
        resolution_status = ResolutionStatus.RESOLVED

    is_composite = len(ordered_src_names) > 1

    enforcement = (
        ConstraintEnforcementStatus.ENFORCED
        if getattr(fk, "is_enforced", True)
        else ConstraintEnforcementStatus.NOT_ENFORCED
    )
    validation = (
        ConstraintValidationStatus.VALIDATED
        if getattr(fk, "is_validated", True)
        else ConstraintValidationStatus.NOT_VALIDATED
    )

    deferrability = getattr(fk, "deferrability", None)
    if deferrability is None and getattr(fk, "is_deferrable", False):
        deferrability = "DEFERRABLE"

    match_type = getattr(fk, "match_type", None)

    return ReconstructedForeignKey(
        object_id=fk.id,
        source_table_id=source_table_id,
        native_name=fk.name,
        source_column_ids=tuple(ordered_src_ids),
        source_column_names=tuple(ordered_src_names),
        referenced_table_id=resolved_target_id,
        referenced_namespace=ref_ns,
        referenced_table_name=ref_table_name,
        referenced_column_names=tuple(ref_cols),
        referenced_column_ids=tuple(resolved_ref_col_ids),
        is_composite=is_composite,
        on_update=fk.on_update,
        on_delete=fk.on_delete,
        match_type=match_type,
        deferrability=deferrability,
        enforcement_status=enforcement,
        validation_status=validation,
        resolution_status=resolution_status,
        is_cross_namespace=is_cross_ns,
        provenance=fk.provenance,
    )


def reconstruct_foreign_keys(
    fks: Sequence[CanonicalForeignKey],
    source_table_id: ObjectId,
    source_namespace: str,
    columns: Sequence[ReconstructedColumn],
    registry: ObjectRegistry | None = None,
) -> tuple[ReconstructedForeignKey, ...]:
    """Reconstruct all foreign keys for a table."""
    reconstructed = [
        reconstruct_foreign_key(fk, source_table_id, source_namespace, columns, registry)
        for fk in fks
    ]
    # Sort deterministically by (name or '', source_column_names, referenced_table_name)
    reconstructed.sort(
        key=lambda k: (k.native_name or "", k.source_column_names, k.referenced_table_name)
    )
    return tuple(reconstructed)
