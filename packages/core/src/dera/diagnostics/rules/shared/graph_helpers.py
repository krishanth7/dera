"""DERA Diagnostics — Shared Graph and Dependency Resolution Helpers.

Provides deterministic utilities for resolving, constructing, and querying
ForeignKeyGraph and DependencyAnalysisResult structures from a DiagnosticContext.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext

type ObjectId = str


def resolve_graph(context: DiagnosticContext) -> Any | None:
    """Deterministically extracts or constructs a ForeignKeyGraph from context.

    Order of resolution:
    1. Direct context.graph instance.
    2. Derived from context.schema.database via ForeignKeyGraphBuilder.from_canonical.
    3. Derived from context.snapshot.schema.database.
    """
    if context.graph is not None:
        return context.graph

    if context.schema is not None:
        db = getattr(context.schema, "database", None)
        if db is not None:
            try:
                from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder

                return ForeignKeyGraphBuilder.from_canonical(db)
            except Exception:
                return None

    if context.snapshot is not None:
        snap_schema = getattr(context.snapshot, "schema", None)
        if snap_schema is not None:
            db = getattr(snap_schema, "database", None)
            if db is not None:
                try:
                    from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder

                    return ForeignKeyGraphBuilder.from_canonical(db)
                except Exception:
                    return None

    return None


def resolve_dependencies(context: DiagnosticContext) -> Any | None:
    """Deterministically extracts or computes a DependencyAnalysisResult from context.

    Order of resolution:
    1. Direct context.dependencies instance.
    2. Computed via DependencyAnalyzer from resolved ForeignKeyGraph.
    """
    if context.dependencies is not None:
        return context.dependencies

    graph = resolve_graph(context)
    if graph is None or len(graph.nodes) == 0:
        return None

    try:
        from dera.reverse_engineering.dependencies.analyzer import DependencyAnalyzer

        analyzer = DependencyAnalyzer()
        return analyzer.analyze(graph, schema=context.schema)
    except Exception:
        return None


def get_table_node_map(graph: Any) -> dict[str, Any]:
    """Returns a deterministic mapping of table node ObjectId to TableNode."""
    return {str(n.object_id): n for n in graph.nodes}


def get_table_name_lookup(graph: Any) -> dict[tuple[str, str], Any]:
    """Returns a mapping of (namespace.lower(), name.lower()) to TableNode."""
    return {(n.namespace_name.lower(), n.native_name.lower()): n for n in graph.nodes}


def compute_reverse_reachability(
    target_node_id: str,
    dependent_adj: dict[str, Sequence[str]],
    max_depth: int = 10,
    max_nodes: int = 1000,
) -> tuple[tuple[str, ...], int]:
    """Computes downstream reverse reachability (all tables that depend on target_node_id).

    Args:
        target_node_id: Root table whose dependents are explored.
        dependent_adj: Parent -> children adjacency mapping (downstream dependents).
        max_depth: Traversal depth ceiling.
        max_nodes: Resource ceiling on total reached nodes.

    Returns:
        Tuple of (deterministically sorted reachable dependent node ObjectIds, maximum depth reached).
    """
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(target_node_id, 0)])
    max_reached_depth = 0

    while queue and len(visited) < max_nodes:
        curr_id, depth = queue.popleft()
        if depth > max_reached_depth:
            max_reached_depth = depth

        if depth >= max_depth:
            continue

        for child_id in dependent_adj.get(curr_id, ()):
            if child_id not in visited and child_id != target_node_id:
                visited.add(child_id)
                queue.append((child_id, depth + 1))

    sorted_dependents = tuple(sorted(visited))
    return sorted_dependents, max_reached_depth


def group_parallel_edges(
    edges: Sequence[Any],
) -> dict[tuple[str, str], list[Any]]:
    """Groups foreign key edges by (source_table_id, referenced_table_id) pair.

    Identifies parallel relationships between the same pair of tables.
    """
    grouped: dict[tuple[str, str], list[Any]] = {}
    for edge in edges:
        if edge.referenced_table_id is not None:
            pair = (str(edge.source_table_id), str(edge.referenced_table_id))
            grouped.setdefault(pair, []).append(edge)
    return grouped


def resolve_tables(context: DiagnosticContext) -> tuple[Any, ...]:
    """Deterministically extracts all canonical tables from DiagnosticContext."""
    if context.schema is not None:
        if hasattr(context.schema, "tables") and context.schema.tables:
            return tuple(context.schema.tables)
        db = getattr(context.schema, "database", None)
        if db is not None:
            if hasattr(db, "all_tables"):
                return tuple(db.all_tables())
            if hasattr(db, "tables"):
                return tuple(db.tables)
        if hasattr(context.schema, "all_tables"):
            return tuple(context.schema.all_tables())

    if context.snapshot is not None:
        snap_schema = getattr(context.snapshot, "schema_representation", None) or getattr(
            context.snapshot, "schema", None
        )
        if snap_schema is not None:
            if hasattr(snap_schema, "tables") and snap_schema.tables:
                return tuple(snap_schema.tables)
            db = getattr(snap_schema, "database", None)
            if db is not None:
                if hasattr(db, "all_tables"):
                    return tuple(db.all_tables())
                if hasattr(db, "tables"):
                    return tuple(db.tables)

    return ()


def resolve_namespaces(context: DiagnosticContext) -> tuple[Any, ...]:
    """Deterministically extracts all canonical namespaces from DiagnosticContext."""
    if context.schema is not None:
        if hasattr(context.schema, "namespaces") and context.schema.namespaces:
            return tuple(context.schema.namespaces)
        db = getattr(context.schema, "database", None)
        if db is not None and hasattr(db, "namespaces") and db.namespaces:
            return tuple(db.namespaces)

    if context.snapshot is not None:
        snap_schema = getattr(context.snapshot, "schema_representation", None) or getattr(
            context.snapshot, "schema", None
        )
        if snap_schema is not None:
            if hasattr(snap_schema, "namespaces") and snap_schema.namespaces:
                return tuple(snap_schema.namespaces)
            db = getattr(snap_schema, "database", None)
            if db is not None and hasattr(db, "namespaces") and db.namespaces:
                return tuple(db.namespaces)

    return ()
