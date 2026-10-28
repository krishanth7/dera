"""Tests for TableNode creation, lookup, and representation."""

from __future__ import annotations

from dera.metadata.enums import MetadataCompleteness, TableType
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.nodes import TableNode

from tests.reverse_engineering.phase_6_3.fixtures import (
    make_graph_provenance,
    make_simple_fk_schema,
)


def test_table_node_creation_and_repr():
    prov = make_graph_provenance()
    node = TableNode(
        object_id="dera:table:t1",
        native_name="accounts",
        namespace_name="finance",
        table_type=TableType.TABLE,
        column_count=8,
        primary_key_columns=("acc_id",),
        completeness=MetadataCompleteness.COMPLETE,
        provenance=prov,
    )
    assert node.fully_qualified_name == "finance.accounts"
    assert "finance.accounts" in repr(node)
    assert node.column_count == 8
    assert node.primary_key_columns == ("acc_id",)


def test_table_node_lookup_by_id_and_name():
    db = make_simple_fk_schema()
    graph = ForeignKeyGraphBuilder.from_canonical(db)

    node_by_name = graph.get_node_by_name("customers", "public")
    assert node_by_name is not None

    node_by_id = graph.get_node(node_by_name.object_id)
    assert node_by_id == node_by_name

    assert graph.get_node_by_name("nonexistent") is None
    assert graph.get_node("dera:table:invalid_id") is None
