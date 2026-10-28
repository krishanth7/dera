"""Unique constraint reconstruction for Phase 6.2 Structural Reconstruction.

Preserves exact ordered column sequences for single and composite unique constraints,
distinguishing table-level constraints from secondary indexes and capturing NULL semantics.
"""

from collections.abc import Sequence

from dera.metadata.enums import ConstraintType
from dera.metadata.identity import ObjectId
from dera.metadata.models import CanonicalConstraint
from dera.reverse_engineering.reconstruction.errors import (
    ConstraintOwnershipError,
    UniqueConstraintReconstructionError,
)
from dera.reverse_engineering.reconstruction.models import (
    ConstraintEnforcementStatus,
    ReconstructedColumn,
    ReconstructedUniqueConstraint,
)


def reconstruct_unique_constraint(
    constraint: CanonicalConstraint,
    owning_table_id: ObjectId,
    columns: Sequence[ReconstructedColumn],
) -> ReconstructedUniqueConstraint:
    """Reconstruct a single unique constraint, preserving ordered column sequences."""
    if constraint.constraint_type != ConstraintType.UNIQUE:
        raise UniqueConstraintReconstructionError(
            f"Expected UNIQUE constraint type, got '{constraint.constraint_type}'."
        )

    constraint_parent = getattr(constraint, "parent_table_id", None) or getattr(
        constraint, "table_id", None
    )
    if constraint_parent and constraint_parent != owning_table_id:
        raise ConstraintOwnershipError(
            f"Unique constraint '{constraint.name or constraint.id}' parent table '{constraint_parent}' does not match owning table '{owning_table_id}'."
        )

    col_by_name = {col.native_name: col for col in columns}
    col_by_id = {col.object_id: col for col in columns}

    ordered_col_ids: list[ObjectId] = []
    ordered_col_names: list[str] = []

    uq_cols = getattr(constraint, "columns", None) or ()
    uq_col_ids = getattr(constraint, "column_ids", None) or ()

    if uq_cols:
        for cname in uq_cols:
            col = col_by_name.get(cname)
            if col is None:
                raise ConstraintOwnershipError(
                    f"Unique constraint '{constraint.name or constraint.id}' column '{cname}' does not belong to table '{owning_table_id}'."
                )
            ordered_col_names.append(col.native_name)
            ordered_col_ids.append(col.object_id)
    elif uq_col_ids:
        for cid in uq_col_ids:
            col = col_by_id.get(cid)
            if col is None:
                raise ConstraintOwnershipError(
                    f"Unique constraint '{constraint.name or constraint.id}' column ObjectId '{cid}' does not belong to table '{owning_table_id}'."
                )
            ordered_col_ids.append(col.object_id)
            ordered_col_names.append(col.native_name)
    else:
        raise UniqueConstraintReconstructionError(
            f"Unique constraint '{constraint.id}' contains no columns."
        )

    is_composite = len(ordered_col_names) > 1

    extra = getattr(constraint, "extra_metadata", None) or {}
    null_distinct = extra.get("null_distinct")
    enforced = (
        ConstraintEnforcementStatus.ENFORCED
        if getattr(constraint, "is_enforced", True) and extra.get("is_enforced", True)
        else ConstraintEnforcementStatus.NOT_ENFORCED
    )

    return ReconstructedUniqueConstraint(
        object_id=constraint.id,
        owning_table_id=owning_table_id,
        native_name=constraint.name,
        is_composite=is_composite,
        column_ids=tuple(ordered_col_ids),
        column_names=tuple(ordered_col_names),
        enforcement_status=enforced,
        null_distinct=null_distinct,
        provenance=constraint.provenance,
    )


def reconstruct_unique_constraints(
    constraints: Sequence[CanonicalConstraint],
    owning_table_id: ObjectId,
    columns: Sequence[ReconstructedColumn],
) -> tuple[ReconstructedUniqueConstraint, ...]:
    """Reconstruct all unique constraints for a table, sorted deterministically."""
    unique_list = [c for c in constraints if c.constraint_type == ConstraintType.UNIQUE]
    reconstructed = [
        reconstruct_unique_constraint(c, owning_table_id, columns) for c in unique_list
    ]
    reconstructed.sort(key=lambda u: (u.native_name or "", u.column_names))
    return tuple(reconstructed)
