"""Security and resource bounding tests for Phase 6.3 Foreign Key Relationship Graph."""

from __future__ import annotations

import pytest
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge
from dera.reverse_engineering.graph.errors import (
    GraphResourceLimitError,
    GraphSerializationError,
)
from dera.reverse_engineering.graph.limits import GraphResourceLimits
from dera.reverse_engineering.graph.nodes import TableNode
from dera.reverse_engineering.graph.serialization import deserialize_graph_from_json

from tests.reverse_engineering.phase_6_3.fixtures import make_graph_provenance


def test_sql_injection_attempt_in_identifiers_treated_as_literal():
    """Verify malicious SQL injection strings in constraint and table names are inert data strings."""
    prov = make_graph_provenance()
    builder = ForeignKeyGraphBuilder(
        database_id="dera:database:sec_db", database_name="sec_db", engine="postgresql"
    )

    malicious_tbl = "users'; DROP TABLE users; --"
    malicious_fk = "fk_malicious'; DROP DATABASE prod; --"
    node1 = TableNode(object_id="dera:table:1", native_name=malicious_tbl, provenance=prov)
    node2 = TableNode(object_id="dera:table:2", native_name="orders", provenance=prov)
    builder.add_node(node1)
    builder.add_node(node2)

    pair = ColumnPairMapping(source_column_name="uid", referenced_column_name="id", ordinal_position=1)
    edge = ForeignKeyEdge(
        object_id="dera:foreign_key:1",
        native_name=malicious_fk,
        source_table_id=node2.object_id,
        referenced_table_id=node1.object_id,
        source_table_name="orders",
        referenced_table_name=malicious_tbl,
        column_pairs=(pair,),
        provenance=prov,
    )
    builder.add_edge(edge)

    graph = builder.build()
    retrieved_node = graph.get_node(node1.object_id)
    assert retrieved_node is not None
    assert retrieved_node.native_name == malicious_tbl

    retrieved_edge = graph.get_edge(edge.object_id)
    assert retrieved_edge is not None
    assert retrieved_edge.native_name == malicious_fk


def test_resource_limits_max_nodes():
    """Verify builder rejects inputs exceeding max_nodes limit."""
    prov = make_graph_provenance()
    limits = GraphResourceLimits(max_nodes=2)
    builder = ForeignKeyGraphBuilder(
        database_id="dera:database:sec", database_name="sec", engine="postgresql", limits=limits
    )

    builder.add_node(TableNode(object_id="dera:table:1", native_name="t1", provenance=prov))
    builder.add_node(TableNode(object_id="dera:table:2", native_name="t2", provenance=prov))

    with pytest.raises(GraphResourceLimitError, match="max_nodes"):
        builder.add_node(TableNode(object_id="dera:table:3", native_name="t3", provenance=prov))


def test_resource_limits_max_edges():
    """Verify builder rejects inputs exceeding max_edges limit."""
    prov = make_graph_provenance()
    limits = GraphResourceLimits(max_edges=1)
    builder = ForeignKeyGraphBuilder(
        database_id="dera:database:sec", database_name="sec", engine="postgresql", limits=limits
    )

    n1 = TableNode(object_id="dera:table:1", native_name="t1", provenance=prov)
    n2 = TableNode(object_id="dera:table:2", native_name="t2", provenance=prov)
    builder.add_node(n1)
    builder.add_node(n2)

    p = ColumnPairMapping(source_column_name="c1", referenced_column_name="c2", ordinal_position=1)
    e1 = ForeignKeyEdge(object_id="dera:fk:1", native_name="fk1", source_table_id=n1.object_id, referenced_table_id=n2.object_id, source_table_name="t1", referenced_table_name="t2", column_pairs=(p,), provenance=prov)
    e2 = ForeignKeyEdge(object_id="dera:fk:2", native_name="fk2", source_table_id=n1.object_id, referenced_table_id=n2.object_id, source_table_name="t1", referenced_table_name="t2", column_pairs=(p,), provenance=prov)

    builder.add_edge(e1)
    with pytest.raises(GraphResourceLimitError, match="max_edges"):
        builder.add_edge(e2)


def test_no_arbitrary_code_execution_during_deserialization():
    """Verify deserialization does not evaluate executable Python objects."""
    exploit_payload = '{"contract_version": "1.0.0", "database_id": "d", "database_name": "d", "engine": "postgresql", "nodes": [], "edges": [], "__class__": "os.system"}'
    with pytest.raises(GraphSerializationError):
        deserialize_graph_from_json(exploit_payload)
