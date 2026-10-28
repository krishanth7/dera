"""DERA Reverse Engineering — Phase 6.4 Dependency Analysis Errors.

Defines a strongly typed exception hierarchy for dependency analysis, topological sorting,
cycle detection, and graph condensation.
"""

from __future__ import annotations


class DependencyAnalysisError(Exception):
    """Base exception for all Phase 6.4 dependency analysis errors."""


class CyclicDependencyError(DependencyAnalysisError):
    """Raised when an unresolvable or unexpected circular dependency is detected."""

    def __init__(self, message: str, cycle_ids: list[str] | tuple[str, ...] | None = None) -> None:
        super().__init__(message)
        self.cycle_ids = tuple(cycle_ids) if cycle_ids is not None else ()


class DependencyResourceLimitError(DependencyAnalysisError):
    """Raised when an analysis operation exceeds configured resource limits."""


class DependencyValidationError(DependencyAnalysisError):
    """Raised when a dependency model fails integrity validation in strict mode."""


class UnresolvableOrderError(DependencyAnalysisError):
    """Raised when a topological or migration order cannot be resolved."""


class DependencySerializationError(DependencyAnalysisError):
    """Raised when serialization or deserialization of dependency structures fails."""
