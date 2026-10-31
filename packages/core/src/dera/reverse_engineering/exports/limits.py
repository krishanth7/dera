"""DERA Reverse Engineering — Phase 6.6 Export Resource Limits.

Defines deterministic resource bounds enforcing computational and storage limits
to protect against Denial-of-Service (DoS) and memory exhaustion.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExportResourceLimits(BaseModel):
    """Resource limits and circuit breakers for export generation."""

    model_config = {"frozen": True, "extra": "forbid"}

    max_export_bytes: int = Field(
        default=50 * 1024 * 1024,  # 50 MB
        description="Maximum size in bytes of a generated export artifact.",
    )
    max_table_count: int = Field(
        default=5_000,
        description="Maximum number of tables allowed in a single export request.",
    )
    max_column_count: int = Field(
        default=50_000,
        description="Maximum number of columns allowed in a single export request.",
    )
    max_edge_count: int = Field(
        default=25_000,
        description="Maximum number of relationship graph edges allowed in a single export.",
    )
    max_traversal_depth: int = Field(
        default=32,
        description="Maximum graph traversal depth allowed for subgraph exports.",
    )
    max_execution_duration_seconds: float = Field(
        default=60.0,
        description="Maximum allowable duration in seconds for in-memory export generation.",
    )


DEFAULT_EXPORT_LIMITS = ExportResourceLimits()
