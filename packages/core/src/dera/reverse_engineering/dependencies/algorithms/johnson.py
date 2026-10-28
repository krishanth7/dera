"""DERA Reverse Engineering — Deterministic Elementary Cycle Enumerator.

Implements bounded elementary directed cycle discovery within strongly connected components,
enforcing deterministic path exploration and circuit breaker limits.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence

from dera.metadata.identity import ObjectId
from dera.reverse_engineering.dependencies.models import (
    BreakabilityStrategy,
    CycleInstance,
    CycleKind,
    DependencyEdge,
)
from dera.reverse_engineering.dependencies.ordering import (
    canonicalize_cycle_nodes,
    sort_cycle_instances,
)


def find_elementary_cycles(
    scc_nodes: Sequence[ObjectId],
    adjacency: Mapping[ObjectId, Sequence[ObjectId]],
    edges_by_pair: Mapping[tuple[ObjectId, ObjectId], Sequence[DependencyEdge]],
    self_loops: set[ObjectId] | None = None,
    max_cycles: int = 1_000,
) -> tuple[tuple[CycleInstance, ...], bool]:
    """Find all elementary cycles within an SCC up to max_cycles.

    Args:
        scc_nodes: Sequence of nodes belonging to the cyclic SCC.
        adjacency: Outgoing adjacency mapping.
        edges_by_pair: Map from (src_id, tgt_id) to available DependencyEdge list.
        self_loops: Set of self-referencing node ObjectIds.
        max_cycles: Circuit-breaker ceiling for discovered cycles.

    Returns:
        Tuple of (sorted CycleInstance models, truncated_boolean).
    """
    loops = self_loops or set()
    node_set = set(scc_nodes)
    discovered_cycles: list[tuple[ObjectId, ...]] = []
    seen_canonical_cycles: set[tuple[str, ...]] = set()
    truncated = False

    # 1. Handle self-loops
    for node in sorted(scc_nodes, key=lambda n: str(n)):
        if node in loops:
            canon = canonicalize_cycle_nodes((node,))
            key = tuple(str(n) for n in canon)
            if key not in seen_canonical_cycles:
                seen_canonical_cycles.add(key)
                discovered_cycles.append(canon)
                if len(discovered_cycles) >= max_cycles:
                    truncated = True
                    break

    if truncated or len(scc_nodes) < 2:
        return _build_cycle_instances(discovered_cycles, edges_by_pair), truncated

    # 2. Deterministic DFS cycle discovery within the induced SCC subgraph
    sorted_scc_nodes = sorted(scc_nodes, key=lambda n: str(n))
    sub_adj: dict[ObjectId, list[ObjectId]] = {
        u: sorted([v for v in adjacency.get(u, ()) if v in node_set and v != u], key=lambda v: str(v))
        for u in sorted_scc_nodes
    }

    visited_path: list[ObjectId] = []
    in_path: set[ObjectId] = set()

    def dfs(current: ObjectId, start_node: ObjectId) -> None:
        nonlocal truncated
        if truncated:
            return

        visited_path.append(current)
        in_path.add(current)

        for neighbor in sub_adj.get(current, []):
            if str(neighbor) < str(start_node):
                # To prevent duplicate permutations, start_node must be the lowest in the cycle
                continue
            if neighbor == start_node:
                # Cycle closed!
                cycle_tuple = tuple(visited_path)
                canon = canonicalize_cycle_nodes(cycle_tuple)
                key = tuple(str(n) for n in canon)
                if key not in seen_canonical_cycles:
                    seen_canonical_cycles.add(key)
                    discovered_cycles.append(canon)
                    if len(discovered_cycles) >= max_cycles:
                        truncated = True
                        break
            elif neighbor not in in_path:
                dfs(neighbor, start_node)
                if truncated:
                    break

        in_path.remove(current)
        visited_path.pop()

    for start_node in sorted_scc_nodes:
        if truncated:
            break
        dfs(start_node, start_node)

    cycle_instances = _build_cycle_instances(discovered_cycles, edges_by_pair)
    return sort_cycle_instances(cycle_instances), truncated


def _build_cycle_instances(
    raw_cycles: Sequence[tuple[ObjectId, ...]],
    edges_by_pair: Mapping[tuple[ObjectId, ObjectId], Sequence[DependencyEdge]],
) -> list[CycleInstance]:
    """Convert raw node tuples into verified CycleInstance models with breakability analysis."""
    instances: list[CycleInstance] = []

    for nodes in raw_cycles:
        n_count = len(nodes)
        edge_ids: list[str] = []
        break_edges: list[str] = []
        has_nullable = False
        has_deferrable = False

        if n_count == 1:
            kind = CycleKind.SELF_REFERENCING
            # Self-loop edge
            pair_edges = edges_by_pair.get((nodes[0], nodes[0]), ())
            for edge in pair_edges:
                edge_ids.append(edge.edge_id)
                if edge.is_nullable:
                    break_edges.append(edge.edge_id)
                    has_nullable = True
                elif edge.is_deferrable:
                    break_edges.append(edge.edge_id)
                    has_deferrable = True
        elif n_count == 2:
            kind = CycleKind.MUTUAL
            for i in range(2):
                src = nodes[i]
                tgt = nodes[(i + 1) % 2]
                pair_edges = edges_by_pair.get((src, tgt), ())
                for edge in pair_edges:
                    edge_ids.append(edge.edge_id)
                    if edge.is_nullable:
                        break_edges.append(edge.edge_id)
                        has_nullable = True
                    elif edge.is_deferrable:
                        break_edges.append(edge.edge_id)
                        has_deferrable = True
        else:
            kind = CycleKind.INDIRECT
            for i in range(n_count):
                src = nodes[i]
                tgt = nodes[(i + 1) % n_count]
                pair_edges = edges_by_pair.get((src, tgt), ())
                for edge in pair_edges:
                    edge_ids.append(edge.edge_id)
                    if edge.is_nullable:
                        break_edges.append(edge.edge_id)
                        has_nullable = True
                    elif edge.is_deferrable:
                        break_edges.append(edge.edge_id)
                        has_deferrable = True

        # Break strategy determination
        is_breakable = len(break_edges) > 0
        if has_nullable:
            strategy = BreakabilityStrategy.NULLABLE_FOREIGN_KEY
        elif has_deferrable:
            strategy = BreakabilityStrategy.DEFERRABLE_CONSTRAINT
        elif is_breakable:
            strategy = BreakabilityStrategy.POST_DATA_LOAD_CONSTRAINT
        else:
            strategy = BreakabilityStrategy.UNBREAKABLE

        # Deterministic cycle ID
        cycle_hash_input = ":".join(str(n) for n in nodes)
        cycle_hash = hashlib.sha256(cycle_hash_input.encode("utf-8")).hexdigest()[:16]
        cycle_id = f"cycle-{kind.value}-{cycle_hash}"

        instances.append(
            CycleInstance(
                cycle_id=cycle_id,
                kind=kind,
                node_ids=nodes,
                edge_ids=tuple(sorted(edge_ids)),
                break_edges=tuple(sorted(break_edges)),
                is_breakable=is_breakable,
                recommended_break_strategy=strategy,
            )
        )

    return instances
