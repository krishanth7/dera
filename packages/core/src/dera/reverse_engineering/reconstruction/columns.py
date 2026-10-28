"""Column reconstruction for Phase 6.2 Structural Reconstruction.

Extracts strongly typed, validated ReconstructedColumn representations preserving
exact ordinal order, native type declarations, nullability, inert defaults, and
dialect identity/generated properties.
"""

from collections.abc import Sequence

from dera.metadata.identity import ObjectId
from dera.metadata.models import CanonicalColumn
from dera.reverse_engineering.reconstruction.errors import InvalidColumnDefinitionError
from dera.reverse_engineering.reconstruction.models import (
    NullabilityState,
    ReconstructedColumn,
)
from dera.reverse_engineering.reconstruction.semantics import (
    classify_default_value,
    extract_generated_metadata,
    extract_identity_metadata,
)


def reconstruct_column(
    canonical_col: CanonicalColumn,
    parent_table_id: ObjectId,
    engine: str,
) -> ReconstructedColumn:
    """Reconstruct a single column into its strongly typed, validated representation."""
    if canonical_col.ordinal_position < 1:
        raise InvalidColumnDefinitionError(
            f"Invalid ordinal position {canonical_col.ordinal_position} for column '{canonical_col.name}'. Must be >= 1."
        )

    # Classify nullability without inventing definitive states for missing metadata
    if canonical_col.is_nullable is True:
        nullability = NullabilityState.NULLABLE
    elif canonical_col.is_nullable is False:
        nullability = NullabilityState.NOT_NULLABLE
    else:
        nullability = NullabilityState.UNKNOWN

    default_raw = getattr(canonical_col, "default_expression", None) or getattr(
        canonical_col, "default_value", None
    )
    default_value = classify_default_value(default_raw, engine)
    generated_col = extract_generated_metadata(canonical_col)
    identity_meta = extract_identity_metadata(canonical_col, engine)
    native_type = getattr(canonical_col, "native_data_type", None) or getattr(
        canonical_col, "native_type", "TEXT"
    )
    owning_table_id = getattr(canonical_col, "parent_table_id", None) or parent_table_id

    return ReconstructedColumn(
        object_id=canonical_col.id,
        parent_table_id=owning_table_id,
        native_name=canonical_col.name,
        ordinal_position=canonical_col.ordinal_position,
        native_type=native_type,
        canonical_type=canonical_col.canonical_type,
        nullability=nullability,
        default_value=default_value,
        generated_column=generated_col,
        identity=identity_meta,
        collation=canonical_col.collation,
        comment=canonical_col.comment,
        provenance=canonical_col.provenance,
    )


def reconstruct_columns(
    canonical_cols: Sequence[CanonicalColumn],
    parent_table_id: ObjectId,
    engine: str,
) -> tuple[ReconstructedColumn, ...]:
    """Reconstruct all columns for a table, sorted by source ordinal position.

    Enforces column uniqueness within the table scope.
    """
    seen_names: set[str] = set()
    reconstructed: list[ReconstructedColumn] = []

    for col in canonical_cols:
        if col.name in seen_names:
            raise InvalidColumnDefinitionError(
                f"Duplicate column name '{col.name}' found in table '{parent_table_id}'."
            )
        seen_names.add(col.name)
        reconstructed.append(reconstruct_column(col, parent_table_id, engine))

    # Preserve declared source column order by sorting strictly by ordinal_position
    reconstructed.sort(key=lambda c: (c.ordinal_position, c.native_name))
    return tuple(reconstructed)
