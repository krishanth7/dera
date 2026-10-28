"""Check constraint reconstruction for Phase 6.2 Structural Reconstruction.

Preserves native CHECK expressions as strictly inert text literals, never executing
or evaluating expressions while capturing enforcement and validation states.
"""

from collections.abc import Sequence

from dera.metadata.enums import ConstraintType
from dera.metadata.identity import ObjectId
from dera.metadata.models import CanonicalConstraint
from dera.reverse_engineering.reconstruction.errors import (
    CheckConstraintReconstructionError,
    ConstraintOwnershipError,
)
from dera.reverse_engineering.reconstruction.models import (
    ConstraintEnforcementStatus,
    ConstraintValidationStatus,
    ReconstructedCheckConstraint,
)


def reconstruct_check_constraint(
    constraint: CanonicalConstraint,
    owning_table_id: ObjectId,
) -> ReconstructedCheckConstraint:
    """Reconstruct a single check constraint, preserving the expression as inert text."""
    if constraint.constraint_type != ConstraintType.CHECK:
        raise CheckConstraintReconstructionError(
            f"Expected CHECK constraint type, got '{constraint.constraint_type}'."
        )

    constraint_parent = getattr(constraint, "parent_table_id", None) or getattr(
        constraint, "table_id", None
    )
    if constraint_parent and constraint_parent != owning_table_id:
        raise ConstraintOwnershipError(
            f"Check constraint '{constraint.name or constraint.id}' parent table '{constraint_parent}' does not match owning table '{owning_table_id}'."
        )

    extra = getattr(constraint, "extra_metadata", None) or {}
    expr = (
        getattr(constraint, "check_clause", None)
        or getattr(constraint, "expression", None)
        or extra.get("expression")
        or extra.get("check_clause")
    )
    if not expr or not str(expr).strip():
        raise CheckConstraintReconstructionError(
            f"Check constraint '{constraint.name or constraint.id}' is missing a check expression."
        )

    enforced = (
        ConstraintEnforcementStatus.ENFORCED
        if getattr(constraint, "is_enforced", True) and extra.get("is_enforced", True)
        else ConstraintEnforcementStatus.NOT_ENFORCED
    )
    validated = (
        ConstraintValidationStatus.VALIDATED
        if getattr(constraint, "is_validated", True) and extra.get("is_validated", True)
        else ConstraintValidationStatus.NOT_VALIDATED
    )

    return ReconstructedCheckConstraint(
        object_id=constraint.id,
        owning_table_id=owning_table_id,
        native_name=constraint.name,
        expression=expr.strip(),
        enforcement_status=enforced,
        validation_status=validated,
        provenance=constraint.provenance,
    )


def reconstruct_check_constraints(
    constraints: Sequence[CanonicalConstraint],
    owning_table_id: ObjectId,
) -> tuple[ReconstructedCheckConstraint, ...]:
    """Reconstruct all check constraints for a table, sorted deterministically."""
    check_list = [c for c in constraints if c.constraint_type == ConstraintType.CHECK]
    reconstructed = [reconstruct_check_constraint(c, owning_table_id) for c in check_list]
    reconstructed.sort(key=lambda ck: (ck.native_name or "", ck.expression))
    return tuple(reconstructed)
