"""DERA Reverse Engineering — Phase 6.1 Error Taxonomy.

Defines strongly typed, hierarchical error classes for all schema representation
failures: construction errors, duplicate detection, invalid references, resource
limits, serialization failures, and integrity violations.
"""

from __future__ import annotations

from dera_core.exceptions import DeraError


class SchemaRepresentationError(DeraError):
    """Base error for all Phase 6.1 schema representation failures."""


class SchemaBuilderError(SchemaRepresentationError):
    """Raised when the SchemaBuilder cannot construct a valid schema representation."""


class UnsupportedSchemaContractError(SchemaBuilderError):
    """Raised when the input metadata uses an unsupported contract version."""


class InvalidSchemaInputError(SchemaBuilderError):
    """Raised when the input canonical metadata is structurally invalid."""


class SchemaValidationError(SchemaRepresentationError):
    """Raised when referential integrity validation detects structural inconsistencies."""


class DuplicateRegistrationError(SchemaRepresentationError):
    """Raised when an ObjectId is registered more than once in the object registry.

    This is a strict error: no silent replacement is permitted.
    """

    def __init__(self, object_id: str, object_kind: str) -> None:
        super().__init__(
            f"Duplicate ObjectId registration detected: {object_id!r} (kind={object_kind!r}). "
            "Each canonical object must have a unique stable identity."
        )
        self.object_id = object_id
        self.object_kind = object_kind


class InvalidSchemaReferenceError(SchemaRepresentationError):
    """Raised when a typed reference targets an ObjectId of the wrong kind or
    when a reference cannot be resolved and strict resolution is required.
    """

    def __init__(
        self, reference_id: str, expected_kind: str, actual_kind: str | None = None
    ) -> None:
        if actual_kind:
            msg = (
                f"Reference {reference_id!r} expected kind {expected_kind!r} "
                f"but found {actual_kind!r}."
            )
        else:
            msg = (
                f"Reference {reference_id!r} of expected kind {expected_kind!r} cannot be resolved."
            )
        super().__init__(msg)
        self.reference_id = reference_id
        self.expected_kind = expected_kind
        self.actual_kind = actual_kind


class MissingParentError(SchemaRepresentationError):
    """Raised when a child object references a parent ObjectId that is not registered."""

    def __init__(self, child_id: str, child_kind: str, parent_id: str, parent_kind: str) -> None:
        super().__init__(
            f"Child {child_kind!r} object {child_id!r} references parent {parent_kind!r} "
            f"{parent_id!r} which is not present in the schema registry."
        )
        self.child_id = child_id
        self.child_kind = child_kind
        self.parent_id = parent_id
        self.parent_kind = parent_kind


class SchemaResourceLimitError(SchemaRepresentationError):
    """Raised when schema construction exceeds configured resource bounds."""

    def __init__(self, limit_name: str, limit_value: int, actual_value: int) -> None:
        super().__init__(
            f"Schema resource limit exceeded: {limit_name}={limit_value}, actual={actual_value}."
        )
        self.limit_name = limit_name
        self.limit_value = limit_value
        self.actual_value = actual_value


class SchemaSerializationError(SchemaRepresentationError):
    """Raised when deterministic serialization of a schema representation fails."""
