"""DERA Reverse Engineering — Deterministic Topological Sort & Condensation DAG.

Implements Kahn's algorithm with stable tie-breaking for pure DAGs, dependency level
stratification, and condensation DAG topological ordering for cyclic schemas.
"""

from __future__ import annotations

import heapq
from collections.abc import Mapping, Sequence

from dera.metadata.identity import ObjectId
from dera.reverse_engineering.dependencies.models import (
    CondensationNode,
    DependencyOrdering,
    StronglyConnectedComponent,
    TopologicalLevel,
)
from dera.reverse_engineering.dependencies.ordering import (
    sort_condensation_nodes,
    sort_topological_levels,
)


def compute_topological_ordering(
    all_nodes: Sequence[ObjectId],
    prerequisite_adj: Mapping[ObjectId, Sequence[ObjectId]],
    sccs: Sequence[StronglyConnectedComponent],
) -> tuple[DependencyOrdering, tuple[CondensationNode, ...]]:
    """Compute deterministic topological ordering, level stratification, and condensation DAG.

    Args:
        all_nodes: Sequence of all graph node ObjectIds.
        prerequisite_adj: Mapping from parent/prerequisite ObjectId to child/dependent ObjectIds.
            (i.e. edge points Parent -> Child in creation flow).
        sccs: Precomputed strongly connected components.

    Returns:
        Tuple of (DependencyOrdering, tuple of CondensationNodes).
    """
    sorted_all_nodes = sorted(all_nodes, key=lambda n: str(n))
    node_set = set(sorted_all_nodes)

    # 1. Check if pure DAG
    has_cyclic_scc = any(scc.is_cyclic for scc in sccs)
    is_pure_dag = not has_cyclic_scc

    # 2. Build condensation DAG
    condensation_nodes, scc_to_cond_id = _build_condensation_dag(sccs, prerequisite_adj, node_set)
    condensed_order = _topological_sort_condensation(condensation_nodes)

    if is_pure_dag:
        # Standard Kahn's algorithm with priority queue
        creation_order, levels = _kahn_topological_sort_with_levels(sorted_all_nodes, prerequisite_adj)
        drop_order = tuple(reversed(creation_order))

        ordering = DependencyOrdering(
            is_pure_dag=True,
            creation_order=creation_order,
            drop_order=drop_order,
            levels=levels,
            condensed_order=condensed_order,
            unresolved_cycles_exist=False,
        )
        return ordering, condensation_nodes

    # 3. For cyclic schemas: staged creation order derived from condensation DAG
    staged_creation_order: list[ObjectId] = []
    cond_map = {c.condensation_id: c for c in condensation_nodes}
    levels_list: list[TopologicalLevel] = []

    for level_idx, cond_id in enumerate(condensed_order):
        c_node = cond_map[cond_id]
        sorted_members = tuple(sorted(c_node.member_node_ids, key=lambda n: str(n)))
        staged_creation_order.extend(sorted_members)
        levels_list.append(TopologicalLevel(level=level_idx, node_ids=sorted_members))

    creation_order = tuple(staged_creation_order)
    drop_order = tuple(reversed(creation_order))

    ordering = DependencyOrdering(
        is_pure_dag=False,
        creation_order=creation_order,
        drop_order=drop_order,
        levels=sort_topological_levels(levels_list),
        condensed_order=condensed_order,
        unresolved_cycles_exist=True,
    )
    return ordering, condensation_nodes


def _kahn_topological_sort_with_levels(
    nodes: Sequence[ObjectId],
    prerequisite_adj: Mapping[ObjectId, Sequence[ObjectId]],
) -> tuple[tuple[ObjectId, ...], tuple[TopologicalLevel, ...]]:
    """Execute Kahn's algorithm with min-heap priority and compute execution levels."""
    # Compute in-degrees in creation flow (number of parents/prerequisites a node has)
    in_degree: dict[ObjectId, int] = {n: 0 for n in nodes}
    for u in nodes:
        for v in prerequisite_adj.get(u, ()):
            if v in in_degree:
                in_degree[v] += 1

    # Level assignment: level[node] = max(level[parent]) + 1
    node_level: dict[ObjectId, int] = {}

    # Initialize frontier with nodes having in_degree == 0 (roots / Level 0)
    # Using min-heap on (str(n), n) for stable deterministic ordering
    heap: list[tuple[str, ObjectId]] = []
    for n in nodes:
        if in_degree[n] == 0:
            heapq.heappush(heap, (str(n), n))
            node_level[n] = 0

    creation_order: list[ObjectId] = []

    while heap:
        _, u = heapq.heappop(heap)
        creation_order.append(u)
        current_lvl = node_level[u]

        for v in sorted(prerequisite_adj.get(u, ()), key=lambda x: str(x)):
            if v in in_degree:
                in_degree[v] -= 1
                # Update level for child v
                child_lvl = current_lvl + 1
                if v not in node_level or child_lvl > node_level[v]:
                    node_level[v] = child_lvl

                if in_degree[v] == 0:
                    heapq.heappush(heap, (str(v), v))

    # Stratify into TopologicalLevels
    level_buckets: dict[int, list[ObjectId]] = {}
    for n, lvl in node_level.items():
        level_buckets.setdefault(lvl, []).append(n)

    result_levels: list[TopologicalLevel] = []
    for lvl_idx in sorted(level_buckets.keys()):
        sorted_level_nodes = tuple(sorted(level_buckets[lvl_idx], key=lambda n: str(n)))
        result_levels.append(TopologicalLevel(level=lvl_idx, node_ids=sorted_level_nodes))

    return tuple(creation_order), sort_topological_levels(result_levels)


def _build_condensation_dag(
    sccs: Sequence[StronglyConnectedComponent],
    prerequisite_adj: Mapping[ObjectId, Sequence[ObjectId]],
    node_set: set[ObjectId],
) -> tuple[tuple[CondensationNode, ...], dict[str, str]]:
    """Contract each SCC into a supernode and map inter-component dependencies."""
    node_to_scc_id: dict[ObjectId, str] = {}
    for scc in sccs:
        for n in scc.node_ids:
            node_to_scc_id[n] = scc.scc_id

    # Inter-SCC dependency tracking (parent_scc -> child_scc)
    scc_deps: dict[str, set[str]] = {scc.scc_id: set() for scc in sccs}

    for u in node_set:
        src_scc = node_to_scc_id.get(u)
        if not src_scc:
            continue
        for v in prerequisite_adj.get(u, ()):
            tgt_scc = node_to_scc_id.get(v)
            if tgt_scc and tgt_scc != src_scc:
                # tgt_scc depends on src_scc
                scc_deps[tgt_scc].add(src_scc)

    condensation_nodes: list[CondensationNode] = []
    for scc in sccs:
        c_id = f"cond-{scc.scc_id}"
        dependencies = tuple(sorted(f"cond-{dep}" for dep in scc_deps[scc.scc_id]))
        condensation_nodes.append(
            CondensationNode(
                condensation_id=c_id,
                is_cyclic=scc.is_cyclic,
                member_node_ids=scc.node_ids,
                dependencies=dependencies,
            )
        )

    return sort_condensation_nodes(condensation_nodes), {scc.scc_id: f"cond-{scc.scc_id}" for scc in sccs}


def _topological_sort_condensation(condensation_nodes: Sequence[CondensationNode]) -> tuple[str, ...]:
    """Deterministically sort condensation supernodes using Kahn's algorithm."""
    in_degree: dict[str, int] = {c.condensation_id: 0 for c in condensation_nodes}
    adj: dict[str, list[str]] = {c.condensation_id: [] for c in condensation_nodes}

    for c in condensation_nodes:
        for dep in c.dependencies:
            if dep in adj:
                adj[dep].append(c.condensation_id)
                in_degree[c.condensation_id] += 1

    heap: list[str] = []
    for cid, deg in in_degree.items():
        if deg == 0:
            heapq.heappush(heap, cid)

    order: list[str] = []
    while heap:
        u = heapq.heappop(heap)
        order.append(u)
        for v in sorted(adj.get(u, [])):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                heapq.heappush(heap, v)

    # In case of remaining nodes (should not happen in condensation graph)
    if len(order) < len(condensation_nodes):
        for c in sorted(condensation_nodes, key=lambda x: x.condensation_id):
            if c.condensation_id not in order:
                order.append(c.condensation_id)

    return tuple(order)
