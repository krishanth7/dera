"""Tests for strict deterministic ordering of graph nodes, edges, traversals, and serialization."""

from __future__ import annotations

import random

from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.nodes import TableNode

from tests.reverse_engineering.phase_6_3.fixtures import (
    make_graph_provenance,
)


def test_input_ordering_independence():
    """Verify that inserting table nodes in different orders produces identical graph hashes."""
    prov = make_graph_provenance()
    node_configs = [
        ("dera:table:c", "charlie"),
        ("dera:table:a", "alpha"),
        ("dera:table:b", "bravo"),
        ("dera:table:d", "delta"),
    ]

    hashes: list[str] = []
    for _ in range(5):
        shuffled = list(node_configs)
        random.shuffle(shuffled)

        builder = ForeignKeyGraphBuilder(
            database_id="dera:database:det_db", database_name="det_db", engine="postgresql", provenance=prov
        )
        for oid, name in shuffled:
            builder.add_node(TableNode(object_id=oid, native_name=name, provenance=prov))

        g = builder.build()
        hashes.append(g.compute_hash())

    # All hashes must be bit-for-bit identical
    assert len(set(hashes)) == 1


def test_deterministic_node_and_edge_ordering():
    """Verify nodes are sorted alphabetically by (namespace, table_name, object_id)."""
    prov = make_graph_provenance()
    builder = ForeignKeyGraphBuilder(
        database_id="dera:database:det_db", database_name="det_db", engine="postgresql"
    )

    builder.add_node(TableNode(object_id="dera:table:z", native_name="zebra", provenance=prov))
    builder.add_node(TableNode(object_id="dera:table:a", native_name="apple", provenance=prov))
    builder.add_node(TableNode(object_id="dera:table:m", native_name="mango", provenance=prov))

    graph = builder.build()
    node_names = [n.native_name for n in graph.nodes]
    assert node_names == ["apple", "mango", "zebra"]
