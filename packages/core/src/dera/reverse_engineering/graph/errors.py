"""DERA Reverse Engineering — Phase 6.3 Foreign Key Relationship Graph Error Taxonomy.

Defines strongly typed, hierarchical exception classes for graph construction,
referential integrity, adjacency indexing, bounded traversal, serialization,
and resource limit violations.
"""

from __future__ import annotations

from typing import Any

from dera_core.exceptions import DeraError


class ForeignKeyGraphError(DeraError):
    """Base exception for all foreign key graph operations."""


class GraphBuilderError(ForeignKeyGraphError):
    """Raised when the ForeignKeyGraphBuilder cannot construct a valid relationship graph."""


class UnsupportedGraphContractError(GraphBuilderError):
    """Raised when graph input metadata utilizes an unsupported contract version."""


class InvalidGraphInputError(GraphBuilderError):
    """Raised when input tables or constraints violate structural expectations."""


class GraphValidationError(ForeignKeyGraphError):
    """Raised when strict referential integrity or graph consistency checks fail."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class InvalidNodeError(GraphValidationError):
    """Raised when a table node possesses duplicate identity or invalid namespace."""


class InvalidEdgeError(GraphValidationError):
    """Raised when a foreign key edge possesses invalid source, target, or column mapping."""


class UnresolvedReferenceError(GraphValidationError):
    """Raised when an unresolved foreign key reference cannot be accepted in strict mode."""


class CrossWorkspaceGraphError(GraphValidationError):
    """Raised when multi-tenant isolation is violated by mixing workspaces in a graph."""


class GraphTraversalError(ForeignKeyGraphError):
    """Raised when graph traversal encounters an error or violates traversal parameters."""


class TraversalLimitExceededError(GraphTraversalError):
    """Raised when traversal exceeds maximum allowed depth or visited node counts."""

    def __init__(self, limit_name: str, limit_value: int, actual_value: int) -> None:
        super().__init__(
            f"Graph traversal resource limit exceeded: {limit_name}={limit_value}, actual={actual_value}."
        )
        self.limit_name = limit_name
        self.limit_value = limit_value
        self.actual_value = actual_value


class GraphResourceLimitError(ForeignKeyGraphError):
    """Raised when graph construction or serialization exceeds configured resource bounds."""

    def __init__(self, limit_name: str, limit_value: int, actual_value: int) -> None:
        super().__init__(
            f"Graph resource limit exceeded: {limit_name}={limit_value}, actual={actual_value}."
        )
        self.limit_name = limit_name
        self.limit_value = limit_value
        self.actual_value = actual_value


class GraphSerializationError(ForeignKeyGraphError):
    """Raised when deterministic serialization or deserialization fails."""
