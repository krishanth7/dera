"""DERA Reverse Engineering — Phase 6.3 Bounded Graph Traversal.

Implements strictly bounded, deterministic breadth-first and depth-first traversal algorithms
alongside weakly connected component discovery for foreign key relationship graphs.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.identity import ObjectId
from dera.reverse_engineering.graph.edges import ForeignKeyEdge
from dera.reverse_engineering.graph.errors import TraversalLimitExceededError
from dera.reverse_engineering.graph.limits import GraphResourceLimits

if TYPE_CHECKING:
    from dera.reverse_engineering.graph.adjacency import AdjacencyIndex
    from dera.reverse_engineering.graph.nodes import TableNode


class TraversalDirection(StrEnum):
    """Directionality convention for graph exploration.

    - OUTGOING: Follow declared foreign keys (child -> referenced parent).
    - INCOMING: Follow reverse references (parent <- referencing child).
    - BOTH: Explore undirected reachability (incoming and outgoing).
    """

    OUTGOING = "outgoing"
    INCOMING = "incoming"
    BOTH = "both"


class TraversalStrategy(StrEnum):
    """Exploration ordering strategy."""

    BFS = "bfs"
    DFS = "dfs"


class TraversalStep(BaseModel):
    """Immutable record of an individual node visitation step during traversal."""

    model_config = ConfigDict(frozen=True)

    table_id: ObjectId = Field(..., description="ObjectId of visited table node.")
    depth: int = Field(..., ge=0, description="Hops from starting node.")
    edge: ForeignKeyEdge | None = Field(
        default=None,
        description="Foreign key edge traversed to reach this node, or None for start node.",
    )
    direction: TraversalDirection = Field(
        ...,
        description="Direction along which the edge was traversed to arrive at table_id.",
    )


class TraversalResult(BaseModel):
    """Immutable outcome of a bounded graph traversal."""

    model_config = ConfigDict(frozen=True)

    start_table_id: ObjectId = Field(..., description="Originating node ObjectId.")
    direction: TraversalDirection = Field(..., description="Direction explored.")
    strategy: TraversalStrategy = Field(..., description="Exploration algorithm used.")
    visited_nodes: tuple[ObjectId, ...] = Field(
        default_factory=tuple,
        description="Unique table ObjectIds visited in exact exploration order.",
    )
    traversed_edges: tuple[ForeignKeyEdge, ...] = Field(
        default_factory=tuple,
        description="Unique foreign key edges traversed during exploration.",
    )
    steps: tuple[TraversalStep, ...] = Field(
        default_factory=tuple,
        description="Ordered sequence of visitation steps.",
    )
    max_depth_reached: int = Field(default=0, ge=0, description="Maximum depth level reached.")
    is_truncated: bool = Field(
        default=False,
        description="True if traversal was halted early due to resource limit bounds.",
    )
    truncation_reason: str | None = Field(
        default=None,
        description="Human-readable reason for early termination if truncated.",
    )


def traverse(
    adjacency: AdjacencyIndex,
    start_table_id: ObjectId,
    direction: TraversalDirection = TraversalDirection.OUTGOING,
    strategy: TraversalStrategy = TraversalStrategy.BFS,
    limits: GraphResourceLimits | None = None,
    raise_on_limit: bool = False,
) -> TraversalResult:
    """Executes a bounded, deterministic traversal originating at start_table_id.

    Guarantees:
    - Strictly terminates within specified limits (max_traversal_depth, max_visited_nodes, max_returned_edges).
    - Preserves deterministic visitation ordering using stably sorted node and edge identifiers.
    - Handles self-loops without redundant node addition or infinite looping.
    - Accurately tracks parallel edges.
    """
    effective_limits = limits or GraphResourceLimits()
    max_depth = effective_limits.max_traversal_depth
    max_nodes = effective_limits.max_visited_nodes
    max_edges = effective_limits.max_returned_edges

    visited_set: set[ObjectId] = {start_table_id}
    visited_order: list[ObjectId] = [start_table_id]
    steps: list[TraversalStep] = [
        TraversalStep(
            table_id=start_table_id,
            depth=0,
            edge=None,
            direction=direction,
        )
    ]
    traversed_edges: list[ForeignKeyEdge] = []
    seen_edge_ids: set[ObjectId] = set()
    max_depth_reached = 0
    is_truncated = False
    truncation_reason: str | None = None

    # Worklist stores tuples: (current_node_id, current_depth)
    if strategy == TraversalStrategy.BFS:
        queue: deque[tuple[ObjectId, int]] = deque([(start_table_id, 0)])
        pop_node = queue.popleft
        push_node = queue.append
        has_items = lambda: len(queue) > 0  # noqa: E731
    else:
        stack: list[tuple[ObjectId, int]] = [(start_table_id, 0)]
        pop_node = stack.pop
        push_node = stack.append
        has_items = lambda: len(stack) > 0  # noqa: E731

    while has_items():
        curr_id, curr_depth = pop_node()
        max_depth_reached = max(max_depth_reached, curr_depth)

        if curr_depth >= max_depth:
            continue

        # Collect candidate transitions: (next_node_id, edge, traversed_direction)
        transitions: list[tuple[ObjectId, ForeignKeyEdge, TraversalDirection]] = []

        if direction in (TraversalDirection.OUTGOING, TraversalDirection.BOTH):
            for edge in adjacency.get_outgoing(curr_id):
                if edge.referenced_table_id is not None:
                    transitions.append(
                        (edge.referenced_table_id, edge, TraversalDirection.OUTGOING)
                    )

        if direction in (TraversalDirection.INCOMING, TraversalDirection.BOTH):
            for edge in adjacency.get_incoming(curr_id):
                transitions.append((edge.source_table_id, edge, TraversalDirection.INCOMING))

        # Deterministically sort candidate transitions by target table ID and edge ID
        # For DFS, sorting reversed before pushing ensures deterministic forward visitation order
        transitions.sort(key=lambda t: (str(t[0]), str(t[1].object_id)))
        if strategy == TraversalStrategy.DFS:
            transitions_to_process = list(reversed(transitions))
        else:
            transitions_to_process = transitions

        for next_id, edge, edge_dir in transitions_to_process:
            # Record edge if not yet seen
            if edge.object_id not in seen_edge_ids:
                if len(traversed_edges) >= max_edges:
                    is_truncated = True
                    truncation_reason = f"max_returned_edges limit ({max_edges}) exceeded"
                    if raise_on_limit:
                        raise TraversalLimitExceededError(
                            "max_returned_edges", max_edges, len(traversed_edges) + 1
                        )
                    break
                traversed_edges.append(edge)
                seen_edge_ids.add(edge.object_id)

            if next_id not in visited_set:
                if len(visited_order) >= max_nodes:
                    is_truncated = True
                    truncation_reason = f"max_visited_nodes limit ({max_nodes}) exceeded"
                    if raise_on_limit:
                        raise TraversalLimitExceededError(
                            "max_visited_nodes", max_nodes, len(visited_order) + 1
                        )
                    break

                visited_set.add(next_id)
                visited_order.append(next_id)
                steps.append(
                    TraversalStep(
                        table_id=next_id,
                        depth=curr_depth + 1,
                        edge=edge,
                        direction=edge_dir,
                    )
                )
                push_node((next_id, curr_depth + 1))

        if is_truncated:
            break

    return TraversalResult(
        start_table_id=start_table_id,
        direction=direction,
        strategy=strategy,
        visited_nodes=tuple(visited_order),
        traversed_edges=tuple(traversed_edges),
        steps=tuple(steps),
        max_depth_reached=max_depth_reached,
        is_truncated=is_truncated,
        truncation_reason=truncation_reason,
    )


def find_weakly_connected_components(
    nodes: Iterable[TableNode],
    edges: Iterable[ForeignKeyEdge],
) -> tuple[tuple[ObjectId, ...], ...]:
    """Partitions table nodes into weakly connected components.

    Treats directed foreign key edges as undirected solely for this partitioning operation.
    Returns a deterministic tuple of components, where:
    - Each component is a tuple of table ObjectIds sorted deterministically by string value.
    - Components are stably sorted by their minimum ObjectId.
    """
    node_ids: set[ObjectId] = {node.object_id for node in nodes}
    if not node_ids:
        return ()

    # Build undirected adjacency map
    adj: dict[ObjectId, set[ObjectId]] = {nid: set() for nid in node_ids}
    for edge in edges:
        src = edge.source_table_id
        ref = edge.referenced_table_id
        if ref is not None and src in adj and ref in adj:
            adj[src].add(ref)
            adj[ref].add(src)

    visited: set[ObjectId] = set()
    components: list[tuple[ObjectId, ...]] = []

    # Sort node_ids to guarantee deterministic iteration order
    sorted_node_ids = sorted(node_ids, key=lambda oid: str(oid))

    for start_id in sorted_node_ids:
        if start_id in visited:
            continue

        comp_members: list[ObjectId] = []
        queue: deque[ObjectId] = deque([start_id])
        visited.add(start_id)

        while queue:
            curr = queue.popleft()
            comp_members.append(curr)

            # Stably sort neighbors before queueing
            neighbors = sorted(adj[curr], key=lambda oid: str(oid))
            for nbr in neighbors:
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)

        comp_members.sort(key=lambda oid: str(oid))
        components.append(tuple(comp_members))

    # Sort components deterministically by their first member
    components.sort(key=lambda comp: str(comp[0]))
    return tuple(components)
