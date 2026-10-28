"""Primary key reconstruction for Phase 6.2 Structural Reconstruction.

Preserves exact declared key column sequences for single and composite primary keys,
verifying column ownership against the owning table.
"""

from collections.abc import Sequence

from dera.metadata.enums import ConstraintType
from dera.metadata.identity import ObjectId
from dera.metadata.models import CanonicalConstraint
from dera.reverse_engineering.reconstruction.errors import (
    ConstraintOwnershipError,
    PrimaryKeyReconstructionError,
)
from dera.reverse_engineering.reconstruction.models import (
    ReconstructedColumn,
    ReconstructedPrimaryKey,
)


def reconstruct_primary_key(
    pk_constraint: CanonicalConstraint | None,
    owning_table_id: ObjectId,
    columns: Sequence[ReconstructedColumn],
) -> ReconstructedPrimaryKey | None:
    """Reconstruct a primary key constraint, preserving exact composite key column sequence.

    Validates that every referenced key column exists in the owning table.
    """
    if pk_constraint is None:
        return None

    if pk_constraint.constraint_type != ConstraintType.PRIMARY_KEY:
        raise PrimaryKeyReconstructionError(
            f"Expected PRIMARY_KEY constraint type, got '{pk_constraint.constraint_type}'."
        )

    constraint_parent = getattr(pk_constraint, "parent_table_id", None) or getattr(
        pk_constraint, "table_id", None
    )
    if constraint_parent and constraint_parent != owning_table_id:
        raise ConstraintOwnershipError(
            f"Primary key '{pk_constraint.name or pk_constraint.id}' parent table '{constraint_parent}' does not match owning table '{owning_table_id}'."
        )

    # Build column lookup indices
    col_by_name = {col.native_name: col for col in columns}
    col_by_id = {col.object_id: col for col in columns}

    ordered_column_ids: list[ObjectId] = []
    ordered_column_names: list[str] = []

    pk_cols = getattr(pk_constraint, "columns", None) or ()
    pk_col_ids = getattr(pk_constraint, "column_ids", None) or ()

    # Use column names sequence if available to preserve exact declared key order
    if pk_cols:
        for col_name in pk_cols:
            col = col_by_name.get(col_name)
            if col is None:
                raise ConstraintOwnershipError(
                    f"Primary key column '{col_name}' does not belong to table '{owning_table_id}'."
                )
            ordered_column_names.append(col.native_name)
            ordered_column_ids.append(col.object_id)
    elif pk_col_ids:
        for cid in pk_col_ids:
            col = col_by_id.get(cid)
            if col is None:
                raise ConstraintOwnershipError(
                    f"Primary key column ObjectId '{cid}' does not belong to table '{owning_table_id}'."
                )
            ordered_column_ids.append(col.object_id)
            ordered_column_names.append(col.native_name)
    else:
        raise PrimaryKeyReconstructionError(
            f"Primary key '{pk_constraint.id}' contains no columns."
        )

    is_composite = len(ordered_column_names) > 1

    return ReconstructedPrimaryKey(
        object_id=pk_constraint.id,
        owning_table_id=owning_table_id,
        native_name=pk_constraint.name,
        is_composite=is_composite,
        column_ids=tuple(ordered_column_ids),
        column_names=tuple(ordered_column_names),
        provenance=pk_constraint.provenance,
    )
