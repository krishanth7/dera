"""DERA Comparison — Phase 9.1 Protocols and Abstract Contracts.

Defines the pluggable comparison engine protocol and component interfaces.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from dera.comparison.models import ComparisonConfig, ComparisonReport
from dera.reverse_engineering.snapshots.models import SchemaSnapshot


@runtime_checkable
class SchemaComparisonEngineProtocol(Protocol):
    """Protocol for deterministic schema snapshot comparison engines."""

    def compare(
        self,
        baseline: SchemaSnapshot,
        target: SchemaSnapshot,
        config: ComparisonConfig | None = None,
    ) -> ComparisonReport:
        """Execute a deterministic comparison between two immutable schema snapshots."""
        ...
