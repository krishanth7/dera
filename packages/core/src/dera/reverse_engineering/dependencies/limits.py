"""DERA Reverse Engineering — Phase 6.4 Dependency Resource Limits.

Configures deterministic upper bounds on graph size, recursion depth, cycle enumeration,
and serialized output to prevent denial of service and combinatorial explosions.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DependencyResourceLimits(BaseModel):
    """Resource constraints enforcing deterministic termination for dependency analysis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_nodes: int = Field(
        default=100_000,
        ge=1,
        description="Maximum number of nodes allowed in dependency analysis.",
    )
    max_edges: int = Field(
        default=500_000,
        ge=0,
        description="Maximum number of dependency edges allowed.",
    )
    max_cycles: int = Field(
        default=1_000,
        ge=1,
        description="Circuit-breaker: maximum elementary cycles to enumerate per SCC.",
    )
    max_recursion_depth: int = Field(
        default=10_000,
        ge=10,
        description="Maximum recursion/traversal depth for DFS and SCC algorithms.",
    )
    max_levels: int = Field(
        default=10_000,
        ge=1,
        description="Maximum topological depth levels permitted before truncation.",
    )
    max_serialized_bytes: int = Field(
        default=10_000_000,
        ge=1024,
        description="Maximum payload size for serialized dependency JSON representations.",
    )
