"""DERA Reverse Engineering — Phase 6.4 Dependency Analyzer.

Main orchestrator for dependency analysis, strongly connected component discovery,
elementary cycle enumeration, topological sorting, and dependency metrics.
"""

from __future__ import annotations

from dera.metadata.identity import ObjectId
from dera.reverse_engineering.dependencies.algorithms.cycle_analysis import (
    compile_cycle_report,
)
from dera.reverse_engineering.dependencies.algorithms.johnson import (
    find_elementary_cycles,
)
from dera.reverse_engineering.dependencies.algorithms.metrics import (
    compute_node_metrics,
)
from dera.reverse_engineering.dependencies.algorithms.tarjan import (
    compute_strongly_connected_components,
)
from dera.reverse_engineering.dependencies.algorithms.topological_sort import (
    compute_topological_ordering,
)
from dera.reverse_engineering.dependencies.errors import (
    CyclicDependencyError,
    DependencyResourceLimitError,
)
from dera.reverse_engineering.dependencies.limits import DependencyResourceLimits
from dera.reverse_engineering.dependencies.models import (
    DEPENDENCY_ANALYSIS_CONTRACT_VERSION,
    DependencyAnalysisResult,
    DependencyEdge,
    DependencyKind,
)
from dera.reverse_engineering.dependencies.ordering import sort_dependency_edges
from dera.reverse_engineering.dependencies.validation import (
    ValidationMode,
    validate_dependency_analysis,
)
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.schema import SchemaRepresentation


class DependencyAnalyzer:
    """Orchestrates deterministic dependency resolution and cycle analysis on ForeignKeyGraph."""

    def __init__(self, limits: DependencyResourceLimits | None = None) -> None:
        self.limits = limits or DependencyResourceLimits()

    def analyze(
        self,
        graph: ForeignKeyGraph,
        schema: SchemaRepresentation | None = None,
        mode: ValidationMode = ValidationMode.PERMISSIVE,
        require_dag: bool = False,
    ) -> DependencyAnalysisResult:
        """Execute full dependency analysis on a verified ForeignKeyGraph.

        Args:
            graph: Source foreign key relationship graph from Phase 6.3.
            schema: Optional canonical schema representation for column nullability lookup.
            mode: Validation mode (STRICT or PERMISSIVE).
            require_dag: If True, raises CyclicDependencyError if any cycles are detected.

        Returns:
            Immutable DependencyAnalysisResult contract.

        Raises:
            DependencyResourceLimitError: If node or edge counts exceed configured limits.
            CyclicDependencyError: If require_dag is True and graph contains cycles.
            DependencyValidationError: If validation fails in STRICT mode.
        """
        # 1. Enforce resource limits
        if len(graph.nodes) > self.limits.max_nodes:
            raise DependencyResourceLimitError(
                f"Graph node count ({len(graph.nodes)}) exceeds configured limit ({self.limits.max_nodes})."
            )
        if len(graph.edges) > self.limits.max_edges:
            raise DependencyResourceLimitError(
                f"Graph edge count ({len(graph.edges)}) exceeds configured limit ({self.limits.max_edges})."
            )

        # 2. Extract nodes
        node_ids = tuple(sorted((n.object_id for n in graph.nodes), key=lambda n: str(n)))
        node_set = set(node_ids)

        # 3. Extract dependency edges
        dependency_edges: list[DependencyEdge] = []
        edges_by_pair: dict[tuple[ObjectId, ObjectId], list[DependencyEdge]] = {}
        self_loops: set[ObjectId] = set()

        # Map column nullabilities if schema is provided
        column_nullability: dict[tuple[str, str], bool] = {}
        if schema:
            for ns in schema.namespaces:
                for tbl in ns.tables:
                    for col in tbl.columns:
                        column_nullability[(tbl.name, col.name)] = col.is_nullable

        for edge in graph.edges:
            if not edge.referenced_table_id or edge.referenced_table_id not in node_set:
                # Unresolved edge, skip from graph dependency topological analysis
                continue

            dep_id = edge.source_table_id
            ref_id = edge.referenced_table_id

            if dep_id == ref_id or edge.is_self_referencing:
                self_loops.add(dep_id)

            # Determine nullability of foreign key columns
            is_nullable = bool(edge.extra_metadata.get("is_nullable", False))
            if schema and not is_nullable:
                # If any source column in the FK is nullable, the child row can be inserted with NULL
                for pair in edge.column_pairs:
                    if column_nullability.get(
                        (edge.source_table_name, pair.source_column_name), False
                    ):
                        is_nullable = True
                        break

            column_pairs = tuple(
                (p.source_column_name, p.referenced_column_name) for p in edge.column_pairs
            )

            dep_edge = DependencyEdge(
                edge_id=str(edge.object_id),
                dependent_id=dep_id,
                referenced_id=ref_id,
                kind=DependencyKind.TABLE_FOREIGN_KEY,
                is_nullable=is_nullable,
                is_deferrable=edge.is_deferrable,
                column_pairs=column_pairs,
            )
            dependency_edges.append(dep_edge)
            edges_by_pair.setdefault((dep_id, ref_id), []).append(dep_edge)

        sorted_dep_edges = sort_dependency_edges(dependency_edges)

        # 4. Construct adjacency mappings
        # dependency_adj: child -> parents (upstream prerequisites)
        dependency_adj: dict[ObjectId, list[ObjectId]] = {n: [] for n in node_ids}
        # prerequisite_adj: parent -> children (downstream dependents in creation flow)
        prerequisite_adj: dict[ObjectId, list[ObjectId]] = {n: [] for n in node_ids}

        for edge in sorted_dep_edges:
            dependency_adj[edge.dependent_id].append(edge.referenced_id)
            prerequisite_adj[edge.referenced_id].append(edge.dependent_id)

        # 5. Compute strongly connected components (Tarjan)
        raw_sccs = compute_strongly_connected_components(
            nodes=node_ids,
            adjacency=dependency_adj,
            self_loops=self_loops,
            limits=self.limits,
        )

        # 6. Enumerate elementary cycles within cyclic SCCs (Johnson)
        sccs_with_cycles = []
        for scc in raw_sccs:
            if scc.is_cyclic:
                cycles, _ = find_elementary_cycles(
                    scc_nodes=scc.node_ids,
                    adjacency=dependency_adj,
                    edges_by_pair=edges_by_pair,
                    self_loops=self_loops,
                    max_cycles=self.limits.max_cycles,
                )
                scc = scc.model_copy(update={"cycles": cycles})
            sccs_with_cycles.append(scc)

        # 7. Compile cycle report & refine complex components
        cycle_report, final_sccs = compile_cycle_report(sccs_with_cycles)

        if require_dag and cycle_report.has_cycles:
            cycle_ids = [c.cycle_id for c in cycle_report.cycles]
            raise CyclicDependencyError(
                f"Graph contains {cycle_report.cycle_count} cycle(s), but require_dag was requested.",
                cycle_ids=cycle_ids,
            )

        # 8. Compute topological ordering & condensation DAG
        ordering, condensation_nodes = compute_topological_ordering(
            all_nodes=node_ids,
            prerequisite_adj=prerequisite_adj,
            sccs=final_sccs,
        )

        # 9. Compute node metrics & roots/leaves
        (
            node_metrics,
            root_node_ids,
            leaf_node_ids,
            isolated_node_ids,
        ) = compute_node_metrics(
            nodes=node_ids,
            dependency_adj=dependency_adj,
            dependent_adj=prerequisite_adj,
            sccs=final_sccs,
        )

        # 10. Assemble initial result
        initial_result = DependencyAnalysisResult(
            contract_version=DEPENDENCY_ANALYSIS_CONTRACT_VERSION,
            workspace_id=graph.workspace_id,
            database_id=graph.database_id,
            source_graph_hash=graph.compute_hash(),
            node_count=len(node_ids),
            edge_count=len(sorted_dep_edges),
            is_dag=not cycle_report.has_cycles,
            ordering=ordering,
            cycle_report=cycle_report,
            node_metrics=node_metrics,
            root_node_ids=root_node_ids,
            leaf_node_ids=leaf_node_ids,
            isolated_node_ids=isolated_node_ids,
            condensation_nodes=condensation_nodes,
            validation_findings=(),
        )

        # 11. Run validation
        findings = validate_dependency_analysis(
            result=initial_result,
            edges=sorted_dep_edges,
            mode=mode,
        )

        return initial_result.model_copy(update={"validation_findings": findings})
