"""DERA Reverse Engineering — Phase 6.3 Graph Resource Bounds.

Defines configurable resource bounds and limits applied during foreign key graph
construction, adjacency indexing, deterministic traversal, and JSON serialization.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GraphResourceLimits(BaseModel):
    """Resource bounds applied during relationship graph construction and traversal.

    Protects against denial-of-service, excessive memory consumption,
    and unbounded recursive loops on complex enterprise database schemas.
    """

    model_config = ConfigDict(frozen=True)

    max_nodes: int = Field(
        default=10_000,
        description="Maximum number of table nodes permitted in a single graph.",
    )
    max_edges: int = Field(
        default=50_000,
        description="Maximum number of foreign key edges permitted in a single graph.",
    )
    max_column_pairs: int = Field(
        default=100_000,
        description="Maximum total number of column pair mappings across all edges.",
    )
    max_traversal_depth: int = Field(
        default=50,
        description="Maximum recursion depth allowed during BFS or DFS graph traversal.",
    )
    max_visited_nodes: int = Field(
        default=10_000,
        description="Maximum number of distinct nodes that may be visited during a traversal.",
    )
    max_returned_edges: int = Field(
        default=50_000,
        description="Maximum number of edges returned in a single traversal result.",
    )
    max_serialized_bytes: int = Field(
        default=10_000_000,
        description="Maximum payload size in bytes permitted during JSON deserialization.",
    )
