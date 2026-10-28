"""DERA Reverse Engineering — Deterministic Tarjan SCC Algorithm.

Implements Tarjan's strongly connected components algorithm with strictly deterministic
tie-breaking and self-loop cycle detection.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from dera.metadata.identity import ObjectId
from dera.reverse_engineering.dependencies.models import StronglyConnectedComponent
from dera.reverse_engineering.dependencies.ordering import sort_sccs


def compute_strongly_connected_components(
    nodes: Sequence[ObjectId],
    adjacency: Mapping[ObjectId, Sequence[ObjectId]],
    self_loops: set[ObjectId] | None = None,
) -> tuple[StronglyConnectedComponent, ...]:
    """Compute strongly connected components deterministically using Tarjan's algorithm.

    Args:
        nodes: Sequence of all graph node ObjectIds.
        adjacency: Mapping from node ObjectId to its outgoing neighbor ObjectIds.
        self_loops: Optional set of nodes that have a self-referencing edge to themselves.

    Returns:
        Deterministic tuple of StronglyConnectedComponent models, with cyclic components first.
    """
    loops = self_loops or set()
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
    stack: list[ObjectId] = []
    raw_sccs: list[list[ObjectId]] = []

    def strongconnect(v: ObjectId) -> None:
        nonlocal index
        indices[v] = index
        lowlinks[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)

        for w in sorted_adj.get(v, []):
            if w not in indices:
                # Successor w has not yet been visited; recurse on it
                strongconnect(w)
                lowlinks[v] = min(lowlinks[v], lowlinks[w])
            elif w in on_stack:
                # Successor w is in stack and hence in the current SCC
                lowlinks[v] = min(lowlinks[v], indices[w])

        # If v is a root node, pop the stack and generate an SCC
        if lowlinks[v] == indices[v]:
            scc_members: list[ObjectId] = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc_members.append(w)
                if w == v:
                    break
            raw_sccs.append(scc_members)

    for node in sorted_nodes:
        if node not in indices:
            strongconnect(node)

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
