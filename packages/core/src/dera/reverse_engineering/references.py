"""DERA Reverse Engineering — Phase 6.1 Typed Object References.

Provides typed, resolution-aware references between schema objects.
References preserve the target ObjectId, expected object kind, resolution status,
and source context — without inventing missing targets.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ResolutionStatus(StrEnum):
    """Status of a typed object reference resolution attempt.

    - RESOLVED: Target ObjectId was found in the registry with the expected kind.
    - MISSING: Target ObjectId is not present in the registry.
    - RESTRICTED: Target exists but is not accessible in this workspace scope.
    - UNSUPPORTED: Target kind is not supported by the source engine.
    - AMBIGUOUS: Multiple objects match the reference specification.
    - INVALID: The reference itself is structurally invalid (e.g. malformed ObjectId).
    """

    RESOLVED = "resolved"
    MISSING = "missing"
    RESTRICTED = "restricted"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"
    INVALID = "invalid"


class TypedRef(BaseModel, Generic[T]):  # noqa: UP046
    """A typed, resolution-aware reference to a schema object.

    Preserves:
    - target_id: The canonical ObjectId of the referenced object.
    - expected_kind: The object kind asserted by the referencing context.
    - status: Resolution status after registry lookup.
    - source_context: Optional human-readable description of referencing context.

    Does NOT hold a direct Python reference to the target object to avoid
    circular reference issues in immutable frozen models.
    """

    model_config = ConfigDict(frozen=True)

    target_id: str = Field(
        ...,
        description="Canonical ObjectId of the referenced schema object.",
    )
    expected_kind: str = Field(
        ...,
        description="Expected ObjectKind string of the referenced object.",
    )
    status: ResolutionStatus = Field(
        default=ResolutionStatus.MISSING,
        description="Resolution status after registry lookup.",
    )
    source_context: str | None = Field(
        default=None,
        description="Optional description of the context that declares this reference.",
    )

    @property
    def is_resolved(self) -> bool:
        """True if the reference was successfully resolved in the registry."""
        return self.status == ResolutionStatus.RESOLVED

    @property
    def is_missing(self) -> bool:
        """True if the target ObjectId was not found in the registry."""
        return self.status == ResolutionStatus.MISSING

    def resolve(self) -> TypedRef[T]:
        """Return a copy of this reference marked as RESOLVED."""
        return self.model_copy(update={"status": ResolutionStatus.RESOLVED})

    def mark_missing(self) -> TypedRef[T]:
        """Return a copy of this reference marked as MISSING."""
        return self.model_copy(update={"status": ResolutionStatus.MISSING})

    def mark_restricted(self) -> TypedRef[T]:
        """Return a copy of this reference marked as RESTRICTED."""
        return self.model_copy(update={"status": ResolutionStatus.RESTRICTED})

    def mark_unsupported(self) -> TypedRef[T]:
        """Return a copy of this reference marked as UNSUPPORTED."""
        return self.model_copy(update={"status": ResolutionStatus.UNSUPPORTED})

    def mark_invalid(self) -> TypedRef[T]:
        """Return a copy of this reference marked as INVALID."""
        return self.model_copy(update={"status": ResolutionStatus.INVALID})

    def __str__(self) -> str:
        return f"TypedRef({self.expected_kind}:{self.target_id}, {self.status})"


class ForeignKeyReference(BaseModel):
    """A typed reference representing a verified foreign key relationship.

    Preserves:
    - foreign_key_id: Canonical ObjectId of the foreign key constraint.
    - foreign_key_name: Native or deterministic surrogate name of the FK.
    - source_table_id: Canonical ObjectId of the child table declaring this FK.
    - source_table_name: Native name of the child table.
    - source_columns: Ordered tuple of referencing column names.
    - referenced_table_id: Canonical ObjectId of referenced parent table (None if unresolved).
    - referenced_table_name: Native name of referenced parent table.
    - referenced_schema: Schema name owning the referenced table (if declared).
    - referenced_columns: Ordered tuple of referenced parent column names.
    - on_update: Referential action upon parent row update.
    - on_delete: Referential action upon parent row delete.
    - status: Resolution status of the target table in the schema registry.
    """

    model_config = ConfigDict(frozen=True)

    foreign_key_id: str = Field(
        ...,
        description="Canonical ObjectId of the foreign key constraint.",
    )
    foreign_key_name: str = Field(
        ...,
        description="Native or deterministic surrogate name of the foreign key.",
    )
    source_table_id: str = Field(
        ...,
        description="Canonical ObjectId of the referencing child table.",
    )
    source_table_name: str = Field(
        ...,
        description="Native name of the referencing child table.",
    )
    source_columns: tuple[str, ...] = Field(
        ...,
        description="Ordered tuple of referencing column names in the child table.",
    )
    referenced_table_id: str | None = Field(
        default=None,
        description="Canonical ObjectId of the referenced parent table, if resolved.",
    )
    referenced_table_name: str = Field(
        ...,
        description="Native name of the referenced parent table.",
    )
    referenced_schema: str | None = Field(
        default=None,
        description="Native schema name owning the referenced table, if declared.",
    )
    referenced_columns: tuple[str, ...] = Field(
        ...,
        description="Ordered tuple of referenced column names in the parent table.",
    )
    on_update: str = Field(
        default="NO ACTION",
        description="Referential action upon parent row UPDATE.",
    )
    on_delete: str = Field(
        default="NO ACTION",
        description="Referential action upon parent row DELETE.",
    )
    status: ResolutionStatus = Field(
        default=ResolutionStatus.MISSING,
        description="Resolution status of the target table reference in the registry.",
    )

    @property
    def is_resolved(self) -> bool:
        """True if the target table was successfully resolved in the registry."""
        return self.status == ResolutionStatus.RESOLVED

    def mark_resolved(self, target_table_id: str) -> ForeignKeyReference:
        """Return a copy of this foreign key reference resolved to target table id."""
        return self.model_copy(
            update={
                "referenced_table_id": target_table_id,
                "status": ResolutionStatus.RESOLVED,
            }
        )

    def mark_missing(self) -> ForeignKeyReference:
        """Return a copy marked as missing in registry."""
        return self.model_copy(update={"status": ResolutionStatus.MISSING})

    def mark_restricted(self) -> ForeignKeyReference:
        """Return a copy marked as restricted in current scope."""
        return self.model_copy(update={"status": ResolutionStatus.RESTRICTED})

    def mark_invalid(self) -> ForeignKeyReference:
        """Return a copy marked as invalid."""
        return self.model_copy(update={"status": ResolutionStatus.INVALID})
