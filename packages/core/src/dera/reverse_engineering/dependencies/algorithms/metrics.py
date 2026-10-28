"""DERA Reverse Engineering — Dependency Metrics & Centrality Analysis.

Computes in-degree, out-degree, transitive closure (ancestors and descendants),
dependency depth, and identifies root, leaf, and isolated schema nodes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from dera.metadata.identity import ObjectId
from dera.reverse_engineering.dependencies.models import (
    DependencyNodeMetrics,
    StronglyConnectedComponent,
)


def compute_node_metrics(
    nodes: Sequence[ObjectId],
    dependency_adj: Mapping[ObjectId, Sequence[ObjectId]],  # child -> parents (depends on)
    dependent_adj: Mapping[ObjectId, Sequence[ObjectId]],  # parent -> children (depended on by)
    sccs: Sequence[StronglyConnectedComponent],
) -> tuple[
    dict[str, DependencyNodeMetrics],
    tuple[ObjectId, ...],
    tuple[ObjectId, ...],
    tuple[ObjectId, ...],
]:
    """Compute detailed dependency metrics for all analyzed nodes.

    Args:
        nodes: Sequence of all graph node ObjectIds.
        dependency_adj: Mapping from node to nodes it directly depends on (upstream prerequisites).
        dependent_adj: Mapping from node to nodes that directly depend on it (downstream dependents).
        sccs: Precomputed strongly connected components.

    Returns:
        Tuple of:
          - dict of DependencyNodeMetrics keyed by ObjectId.value
          - sorted tuple of root node ObjectIds
          - sorted tuple of leaf node ObjectIds
          - sorted tuple of isolated node ObjectIds
    """
    sorted_nodes = sorted(nodes, key=lambda n: str(n))

    # Map nodes to cyclic status
    cyclic_nodes: set[ObjectId] = set()
    for scc in sccs:
        if scc.is_cyclic:
            cyclic_nodes.update(scc.node_ids)

    # 1. Direct degrees
    in_degrees: dict[ObjectId, int] = {n: len(set(dependency_adj.get(n, ()))) for n in sorted_nodes}
    out_degrees: dict[ObjectId, int] = {n: len(set(dependent_adj.get(n, ()))) for n in sorted_nodes}

    # 2. Transitive ancestors (all tables node depends on)
    transitive_deps: dict[ObjectId, set[ObjectId]] = {}
    for n in sorted_nodes:
        visited: set[ObjectId] = set()
        queue = list(set(dependency_adj.get(n, ())))
        while queue:
            curr = queue.pop(0)
            if curr not in visited and curr != n:
                visited.add(curr)
                for upstream in dependency_adj.get(curr, ()):
                    if upstream not in visited and upstream != n:
                        queue.append(upstream)
        transitive_deps[n] = visited

    # 3. Transitive descendants (all tables that depend on node)
    transitive_dependents: dict[ObjectId, set[ObjectId]] = {}
    for n in sorted_nodes:
        visited: set[ObjectId] = set()
        queue = list(set(dependent_adj.get(n, ())))
        while queue:
            curr = queue.pop(0)
            if curr not in visited and curr != n:
                visited.add(curr)
                for downstream in dependent_adj.get(curr, ()):
                    if downstream not in visited and downstream != n:
                        queue.append(downstream)
        transitive_dependents[n] = visited

    # 4. Longest path depth from any root (bounded BFS/DFS avoiding cycles)
    depth_levels: dict[ObjectId, int] = {}
    for n in sorted_nodes:
        # Longest simple path in dependency direction
        depth_levels[n] = _compute_max_depth(n, dependency_adj, set())

    # Build metrics map and categorize roots, leaves, isolated
    metrics_map: dict[str, DependencyNodeMetrics] = {}
    roots: list[ObjectId] = []
    leaves: list[ObjectId] = []
    isolated: list[ObjectId] = []

    for n in sorted_nodes:
        in_deg = in_degrees[n]
        out_deg = out_degrees[n]
        is_root = in_deg == 0
        is_leaf = out_deg == 0
        is_iso = is_root and is_leaf
        in_cyc = n in cyclic_nodes

        if is_iso:
            isolated.append(n)
        if is_root:
            roots.append(n)
        if is_leaf:
            leaves.append(n)

        metrics_map[str(n)] = DependencyNodeMetrics(
            node_id=n,
            in_degree=in_deg,
            out_degree=out_deg,
            transitive_dependency_count=len(transitive_deps[n]),
            transitive_dependent_count=len(transitive_dependents[n]),
            depth_level=depth_levels[n],
            is_root=is_root,
            is_leaf=is_leaf,
            is_in_cycle=in_cyc,
        )

    return (
        metrics_map,
        tuple(sorted(roots, key=lambda n: str(n))),
        tuple(sorted(leaves, key=lambda n: str(n))),
        tuple(sorted(isolated, key=lambda n: str(n))),
    )


def _compute_max_depth(
    curr: ObjectId,
    dependency_adj: Mapping[ObjectId, Sequence[ObjectId]],
    visited: set[ObjectId],
) -> int:
    """Recursively compute maximum dependency depth avoiding cycles."""
    parents = [p for p in dependency_adj.get(curr, ()) if p not in visited and p != curr]
    if not parents:
        return 0

    max_p_depth = 0
    new_visited = visited | {curr}
    for p in parents:
        d = 1 + _compute_max_depth(p, dependency_adj, new_visited)
        if d > max_p_depth:
            max_p_depth = d

    return max_p_depth
