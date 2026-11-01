"""DERA Migration — Phase 9.2 Dependency Impact & Blast Radius.

Computes bounded forward and reverse reachability over the canonical foreign key
dependency graph to quantify direct and transitive blast-radius metrics.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.identity import ObjectId
from dera.migration.limits import MigrationRiskLimits

if TYPE_CHECKING:
    from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
    from dera.reverse_engineering.graph.models import ForeignKeyGraph


class DependentObject(BaseModel):
    """A dependent schema entity affected by an upstream structural change."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    object_id: str = Field(description="Canonical ObjectId of the dependent entity.")
    namespace: str = Field(description="Namespace of dependent entity.")
    name: str = Field(description="Native name of dependent entity.")
    dependency_depth: int = Field(description="Topological distance (1 = direct child).")
    is_direct: bool = Field(description="True if directly referencing the target object.")


class BlastRadiusMetrics(BaseModel):
    """Quantified dependency impact metrics for a changed table."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target_table_id: str = Field(description="ObjectId of changed table.")
    direct_dependents_count: int = Field(default=0, description="Count of direct child dependents.")
    transitive_dependents_count: int = Field(default=0, description="Count of indirect transitive dependents.")
    affected_namespaces: tuple[str, ...] = Field(default=(), description="Namespaces containing affected dependents.")
    max_dependency_depth: int = Field(default=0, description="Maximum reachability path length.")
    is_part_of_cycle: bool = Field(default=False, description="True if table participates in a dependency cycle.")
    dependents: tuple[DependentObject, ...] = Field(
        default_factory=tuple,
        description="Ordered sequence of dependent objects.",
    )


class DependencyImpactAnalyzer:
    """Analyzes dependency graph reachability to measure migration blast radius."""

    def __init__(self, limits: MigrationRiskLimits | None = None) -> None:
        self.limits = limits or MigrationRiskLimits()

    def analyze_table_impact(
        self,
        table_id: str,
        graph: ForeignKeyGraph | None,
        dependencies: DependencyAnalysisResult | None = None,
    ) -> BlastRadiusMetrics:
        """Compute blast radius metrics for a changed table."""
        if graph is None:
            return BlastRadiusMetrics(target_table_id=table_id)

        # Build reverse adjacency map: parent -> list of child tables
        # Recall graph direction: edge.source_table_id (child holding FK) -> edge.referenced_table_id (parent)
        reverse_adj: dict[str, list[tuple[str, str, str]]] = {}  # parent -> [(child_id, child_ns, child_name)]
        for edge in graph.edges:
            parent_id = str(getattr(edge, "referenced_table_id", None) or getattr(edge, "target_table_id", ""))
            child_id = str(edge.source_table_id)
            child_ns = edge.source_namespace or ""
            child_name = edge.source_table_name or ""
            if parent_id:
                reverse_adj.setdefault(parent_id, []).append((child_id, child_ns, child_name))

        # BFS for downstream dependents with cycle and depth bounds
        visited: dict[str, int] = {}  # child_id -> min_depth
        dependents: list[DependentObject] = []
        queue: deque[tuple[str, int]] = deque()

        for child_id, c_ns, c_name in reverse_adj.get(table_id, []):
            if child_id != table_id and child_id not in visited:
                visited[child_id] = 1
                queue.append((child_id, 1))
                dependents.append(
                    DependentObject(
                        object_id=child_id,
                        namespace=c_ns,
                        name=c_name,
                        dependency_depth=1,
                        is_direct=True,
                    )
                )

        while queue:
            curr_id, curr_depth = queue.popleft()
            if curr_depth >= self.limits.max_graph_traversal_depth:
                continue

            next_depth = curr_depth + 1
            for child_id, c_ns, c_name in reverse_adj.get(curr_id, []):
                if child_id == table_id or child_id in visited:
                    continue
                self.limits.check_reachable_nodes(len(visited) + 1)
                visited[child_id] = next_depth
                queue.append((child_id, next_depth))
                dependents.append(
                    DependentObject(
                        object_id=child_id,
                        namespace=c_ns,
                        name=c_name,
                        dependency_depth=next_depth,
                        is_direct=False,
                    )
                )

        # Check cyclic participation if DependencyAnalysisResult available
        is_cyclic = False
        if dependencies is not None:
            for cycle in dependencies.cycles:
                if any(str(nid) == table_id for nid in cycle.node_ids):
                    is_cyclic = True
                    break

        # Sort dependents deterministically by (depth, namespace, name, object_id)
        sorted_dependents = tuple(
            sorted(
                dependents,
                key=lambda d: (d.dependency_depth, d.namespace, d.name, d.object_id),
            )
        )
        direct_count = sum(1 for d in sorted_dependents if d.is_direct)
        transitive_count = len(sorted_dependents) - direct_count
        max_depth = max((d.dependency_depth for d in sorted_dependents), default=0)
        affected_ns = tuple(sorted({d.namespace for d in sorted_dependents if d.namespace}))

        return BlastRadiusMetrics(
            target_table_id=table_id,
            direct_dependents_count=direct_count,
            transitive_dependents_count=transitive_count,
            affected_namespaces=affected_ns,
            max_dependency_depth=max_depth,
            is_part_of_cycle=is_cyclic,
            dependents=sorted_dependents,
        )
