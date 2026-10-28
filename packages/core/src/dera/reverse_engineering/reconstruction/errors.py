"""Strongly typed error taxonomy for Phase 6.2 Structural Reconstruction.

All errors inherit from SchemaRepresentationError (and thus DeraError) to maintain
architectural hierarchy and compatibility across core reverse engineering packages.
"""

from typing import Any

from dera.reverse_engineering.errors import SchemaRepresentationError


class StructuralReconstructionError(SchemaRepresentationError):
    """Root exception for all Phase 6.2 structural reconstruction errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class InvalidColumnDefinitionError(StructuralReconstructionError):
    """Raised when a column definition is structurally invalid or contradictory."""

    pass


class InvalidConstraintDefinitionError(StructuralReconstructionError):
    """Raised when a constraint definition is structurally invalid."""

    pass


class PrimaryKeyReconstructionError(InvalidConstraintDefinitionError):
    """Raised when primary key reconstruction encounters an unrecoverable structural error."""

    pass


class ForeignKeyReconstructionError(InvalidConstraintDefinitionError):
    """Raised when foreign key reconstruction encounters mismatched columns or invalid targets."""

    pass


class UniqueConstraintReconstructionError(InvalidConstraintDefinitionError):
    """Raised when a unique constraint contains invalid columns or configuration."""

    pass


class CheckConstraintReconstructionError(InvalidConstraintDefinitionError):
    """Raised when a check constraint definition is missing an expression or corrupt."""

    pass


class ConstraintOwnershipError(StructuralReconstructionError):
    """Raised when a constraint references columns outside of its owning parent table."""

    pass


class StructuralValidationError(StructuralReconstructionError):
    """Raised when strict structural validation fails across the reconstructed schema."""

    pass


class UnsupportedDialectSemanticsError(StructuralReconstructionError):
    """Raised when a database dialect or feature is not recognized by the reconstruction engine."""

    pass
