"""DERA Reverse Engineering — Phase 6.3 Graph Adjacency Indexes.

Provides high-performance, deterministic O(1) indexed lookups for incoming, outgoing,
and pairwise foreign key relationships and neighbor discovery.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.identity import ObjectId
from dera.reverse_engineering.graph.edges import ForeignKeyEdge
from dera.reverse_engineering.graph.nodes import TableNode


class AdjacencyIndex(BaseModel):
    """Immutable bidirectional adjacency index for foreign key relationship graphs.

    Provides constant-time O(1) lookups for:
    - Outgoing foreign keys (child -> parent)
    - Incoming foreign keys (parent <- child)
    - Relationships between specific pairs of tables
    - Distinct deterministic neighbor lookups
    """

    model_config = ConfigDict(frozen=True)

    outgoing: dict[ObjectId, tuple[ForeignKeyEdge, ...]] = Field(
        default_factory=dict,
        description="Maps source table ObjectId to foreign key edges declared by that table.",
    )
    incoming: dict[ObjectId, tuple[ForeignKeyEdge, ...]] = Field(
        default_factory=dict,
        description="Maps referenced table ObjectId to foreign key edges pointing to that table.",
    )
    between: dict[tuple[ObjectId, ObjectId], tuple[ForeignKeyEdge, ...]] = Field(
        default_factory=dict,
        description="Maps (source_table_id, referenced_table_id) to all matching parallel edges.",
    )

    @classmethod
    def build(
        cls,
        nodes: Iterable[TableNode],
        edges: Iterable[ForeignKeyEdge],
    ) -> AdjacencyIndex:
        """Constructs an immutable AdjacencyIndex from node and edge collections.

        Guarantees:
        - Every table node is initialized in both incoming and outgoing maps.
        - Edges with unresolved targets are indexed in outgoing, but omitted from incoming.
        - Parallel edges between identical source/target endpoints are preserved.
        - Order of edges is stably preserved according to edge input sequence.
        """
        out_map: dict[ObjectId, list[ForeignKeyEdge]] = {node.object_id: [] for node in nodes}
        in_map: dict[ObjectId, list[ForeignKeyEdge]] = {node.object_id: [] for node in nodes}
        between_map: dict[tuple[ObjectId, ObjectId], list[ForeignKeyEdge]] = defaultdict(list)

        for edge in edges:
            src_id = edge.source_table_id
            if src_id not in out_map:
                out_map[src_id] = []
            out_map[src_id].append(edge)

            ref_id = edge.referenced_table_id
            if ref_id is not None:
                if ref_id not in in_map:
                    in_map[ref_id] = []
                in_map[ref_id].append(edge)
                between_map[(src_id, ref_id)].append(edge)

        frozen_out = {k: tuple(v) for k, v in out_map.items()}
        frozen_in = {k: tuple(v) for k, v in in_map.items()}
        frozen_between = {k: tuple(v) for k, v in between_map.items()}

        return cls(
            outgoing=frozen_out,
            incoming=frozen_in,
            between=frozen_between,
        )

    def get_outgoing(self, table_id: ObjectId) -> tuple[ForeignKeyEdge, ...]:
        """Returns all foreign key edges declared by the given table."""
        return self.outgoing.get(table_id, ())

    def get_incoming(self, table_id: ObjectId) -> tuple[ForeignKeyEdge, ...]:
        """Returns all foreign key edges pointing to the given table."""
        return self.incoming.get(table_id, ())

    def get_between(
        self,
        source_table_id: ObjectId,
        referenced_table_id: ObjectId,
    ) -> tuple[ForeignKeyEdge, ...]:
        """Returns all foreign key edges connecting source_table_id to referenced_table_id."""
        return self.between.get((source_table_id, referenced_table_id), ())

    def outgoing_neighbors(self, table_id: ObjectId) -> tuple[ObjectId, ...]:
        """Returns unique table ObjectIds referenced by the given table, stably sorted."""
        edges = self.get_outgoing(table_id)
        targets = {e.referenced_table_id for e in edges if e.referenced_table_id is not None}
        return tuple(sorted(targets, key=lambda oid: str(oid)))

    def incoming_neighbors(self, table_id: ObjectId) -> tuple[ObjectId, ...]:
        """Returns unique table ObjectIds that reference the given table, stably sorted."""
        edges = self.get_incoming(table_id)
        sources = {e.source_table_id for e in edges}
        return tuple(sorted(sources, key=lambda oid: str(oid)))

    def all_neighbors(self, table_id: ObjectId) -> tuple[ObjectId, ...]:
        """Returns unique table ObjectIds connected either incoming or outgoing, stably sorted."""
        combined = set(self.outgoing_neighbors(table_id)) | set(self.incoming_neighbors(table_id))
        return tuple(sorted(combined, key=lambda oid: str(oid)))
