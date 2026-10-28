"""DERA Reverse Engineering — Deterministic Tarjan SCC Algorithm.

Implements Tarjan's strongly connected components algorithm with strictly deterministic
tie-breaking and self-loop cycle detection.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from dera.metadata.identity import ObjectId
from dera.reverse_engineering.dependencies.errors import DependencyResourceLimitError
from dera.reverse_engineering.dependencies.limits import DependencyResourceLimits
from dera.reverse_engineering.dependencies.models import StronglyConnectedComponent
from dera.reverse_engineering.dependencies.ordering import sort_sccs


def compute_strongly_connected_components(
    nodes: Sequence[ObjectId],
    adjacency: Mapping[ObjectId, Sequence[ObjectId]],
    self_loops: set[ObjectId] | None = None,
    limits: DependencyResourceLimits | None = None,
) -> tuple[StronglyConnectedComponent, ...]:
    """Compute strongly connected components deterministically using Tarjan's algorithm.

    Args:
        nodes: Sequence of all graph node ObjectIds.
        adjacency: Mapping from node ObjectId to its outgoing neighbor ObjectIds.
        self_loops: Optional set of nodes that have a self-referencing edge to themselves.
        limits: Optional resource limits bounding recursion depth and node counts.

    Returns:
        Deterministic tuple of StronglyConnectedComponent models, with cyclic components first.
    """
    loops = self_loops or set()
    max_depth = limits.max_recursion_depth if limits else None

    # Sort initial nodes deterministically
    sorted_nodes = sorted(nodes, key=lambda n: str(n))

    # Sort adjacency lists deterministically
    sorted_adj: dict[ObjectId, list[ObjectId]] = {
        u: sorted(adjacency.get(u, ()), key=lambda v: str(v)) for u in sorted_nodes
    }

    index = 0
    indices: dict[ObjectId, int] = {}
    lowlinks: dict[ObjectId, int] = {}
    on_stack: set[ObjectId] = set()
    tarjan_stack: list[ObjectId] = []
    raw_sccs: list[list[ObjectId]] = []

    # Iterative Tarjan using an explicit call stack to eliminate Python recursion limits
    for root_node in sorted_nodes:
        if root_node in indices:
            continue

        indices[root_node] = index
        lowlinks[root_node] = index
        index += 1
        tarjan_stack.append(root_node)
        on_stack.add(root_node)

        # Call stack items: [node, neighbor_index]
        call_stack: list[list[int | ObjectId]] = [[root_node, 0]]

        while call_stack:
            if max_depth is not None and len(call_stack) > max_depth:
                raise DependencyResourceLimitError(
                    f"Maximum recursion depth of {max_depth} exceeded during SCC traversal"
                )

            frame = call_stack[-1]
            u: ObjectId = frame[0]  # type: ignore[assignment]
            edge_idx: int = frame[1]  # type: ignore[assignment]
            neighbors = sorted_adj.get(u, [])

            if edge_idx < len(neighbors):
                frame[1] = edge_idx + 1
                w = neighbors[edge_idx]

                if w not in indices:
                    indices[w] = index
                    lowlinks[w] = index
                    index += 1
                    tarjan_stack.append(w)
                    on_stack.add(w)
                    call_stack.append([w, 0])
                elif w in on_stack:
                    lowlinks[u] = min(lowlinks[u], indices[w])
            else:
                call_stack.pop()
                if call_stack:
                    parent_u: ObjectId = call_stack[-1][0]  # type: ignore[assignment]
                    lowlinks[parent_u] = min(lowlinks[parent_u], lowlinks[u])

                if lowlinks[u] == indices[u]:
                    scc_members: list[ObjectId] = []
                    while True:
                        popped = tarjan_stack.pop()
                        on_stack.remove(popped)
                        scc_members.append(popped)
                        if popped == u:
                            break
                    raw_sccs.append(scc_members)

    # Construct strongly typed component models
    result_sccs: list[StronglyConnectedComponent] = []
    for members in raw_sccs:
        sorted_members = tuple(sorted(members, key=lambda n: str(n)))
        is_cyclic = len(sorted_members) > 1 or (
            len(sorted_members) == 1 and sorted_members[0] in loops
        )
        # Deterministic SCC ID derived from member hashes
        member_hash_str = "_".join(str(n)[:12] for n in sorted_members)
        scc_id = f"scc-{member_hash_str}"

        result_sccs.append(
            StronglyConnectedComponent(
                scc_id=scc_id,
                node_ids=sorted_members,
                is_cyclic=is_cyclic,
                cycles=(),  # Populated downstream by cycle analyzer
            )
        )

    return sort_sccs(result_sccs)
