"""DERA Phase 6.2: Structural Reconstruction Package.

Provides deterministic reconstruction of tables, columns, primary keys, foreign keys,
unique constraints, and check constraints preserving exact database semantics,
ordered composite key references, inert expressions, and cross-engine nuances.
"""

from dera.reverse_engineering.reconstruction.builder import (
    StructuralReconstructionBuilder,
    compute_structural_hash,
)
from dera.reverse_engineering.reconstruction.check_constraints import (
    reconstruct_check_constraint,
    reconstruct_check_constraints,
)
from dera.reverse_engineering.reconstruction.columns import (
    reconstruct_column,
    reconstruct_columns,
)
from dera.reverse_engineering.reconstruction.errors import (
    CheckConstraintReconstructionError,
    ConstraintOwnershipError,
    ForeignKeyReconstructionError,
    InvalidColumnDefinitionError,
    InvalidConstraintDefinitionError,
    PrimaryKeyReconstructionError,
    StructuralReconstructionError,
    StructuralValidationError,
    UniqueConstraintReconstructionError,
    UnsupportedDialectSemanticsError,
)
from dera.reverse_engineering.reconstruction.foreign_keys import (
    reconstruct_foreign_key,
    reconstruct_foreign_keys,
)
from dera.reverse_engineering.reconstruction.models import (
    ConstraintEnforcementStatus,
    ConstraintValidationStatus,
    DefaultKind,
    DefaultValueMetadata,
    GeneratedColumnMetadata,
    IdentityMetadata,
    NullabilityState,
    ReconstructedCheckConstraint,
    ReconstructedColumn,
    ReconstructedForeignKey,
    ReconstructedPrimaryKey,
    ReconstructedTable,
    ReconstructedUniqueConstraint,
    ReconstructionMode,
    StructuralReconstructionResult,
    StructuralValidationFinding,
    ValidationSeverity,
)
from dera.reverse_engineering.reconstruction.primary_keys import (
    reconstruct_primary_key,
)
from dera.reverse_engineering.reconstruction.semantics import (
    classify_default_value,
    extract_generated_metadata,
    extract_identity_metadata,
    extract_table_native_attributes,
    normalize_engine_name,
)
from dera.reverse_engineering.reconstruction.tables import (
    reconstruct_table,
)
from dera.reverse_engineering.reconstruction.unique_constraints import (
    reconstruct_unique_constraint,
    reconstruct_unique_constraints,
)
from dera.reverse_engineering.reconstruction.validation import (
    validate_structural_reconstruction,
)

__all__ = [
    # Enums
    "NullabilityState",
    "DefaultKind",
    "ReconstructionMode",
    "ValidationSeverity",
    "ConstraintValidationStatus",
    "ConstraintEnforcementStatus",
    # Models
    "DefaultValueMetadata",
    "GeneratedColumnMetadata",
    "IdentityMetadata",
    "ReconstructedColumn",
    "ReconstructedPrimaryKey",
    "ReconstructedForeignKey",
    "ReconstructedUniqueConstraint",
    "ReconstructedCheckConstraint",
    "ReconstructedTable",
    "StructuralValidationFinding",
    "StructuralReconstructionResult",
    # Builder
    "StructuralReconstructionBuilder",
    "compute_structural_hash",
    # Reconstruction functions
    "reconstruct_table",
    "reconstruct_column",
    "reconstruct_columns",
    "reconstruct_primary_key",
    "reconstruct_foreign_key",
    "reconstruct_foreign_keys",
    "reconstruct_unique_constraint",
    "reconstruct_unique_constraints",
    "reconstruct_check_constraint",
    "reconstruct_check_constraints",
    "validate_structural_reconstruction",
    # Semantics helpers
    "classify_default_value",
    "extract_generated_metadata",
    "extract_identity_metadata",
    "extract_table_native_attributes",
    "normalize_engine_name",
    # Errors
    "StructuralReconstructionError",
    "InvalidColumnDefinitionError",
    "InvalidConstraintDefinitionError",
    "PrimaryKeyReconstructionError",
    "ForeignKeyReconstructionError",
    "UniqueConstraintReconstructionError",
    "CheckConstraintReconstructionError",
    "ConstraintOwnershipError",
    "StructuralValidationError",
    "UnsupportedDialectSemanticsError",
]
