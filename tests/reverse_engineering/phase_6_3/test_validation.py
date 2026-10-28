"""Tests for graph validation rules, severity reporting, and strict mode enforcement."""

from __future__ import annotations

import pytest
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge
from dera.reverse_engineering.graph.errors import GraphBuilderError, GraphValidationError
from dera.reverse_engineering.graph.nodes import TableNode
from dera.reverse_engineering.graph.validation import (
    ValidationMode,
    ValidationSeverity,
    validate_foreign_key_graph,
)

from tests.reverse_engineering.phase_6_3.fixtures import make_graph_provenance


def test_validation_detects_missing_source_node():
    prov = make_graph_provenance()
    node = TableNode(object_id="dera:table:valid", native_name="valid", provenance=prov)
    pair = ColumnPairMapping(
        source_column_name="c1", referenced_column_name="p1", ordinal_position=1
    )
    edge = ForeignKeyEdge(
        object_id="dera:foreign_key:e1",
        native_name="e1",
        source_table_id="dera:table:nonexistent",
        referenced_table_id=node.object_id,
        source_table_name="nonexistent",
        referenced_table_name="valid",
        column_pairs=(pair,),
        provenance=prov,
    )

    findings = validate_foreign_key_graph(
        nodes=(node,), edges=(edge,), mode=ValidationMode.PERMISSIVE
    )
    error_codes = [f.code for f in findings if f.severity == ValidationSeverity.ERROR]
    assert "FKG_MISSING_SOURCE_NODE" in error_codes


def test_validation_strict_mode_raises():
    prov = make_graph_provenance()
    node = TableNode(object_id="dera:table:valid", native_name="valid", provenance=prov)
    pair = ColumnPairMapping(
        source_column_name="c1", referenced_column_name="p1", ordinal_position=1
    )
    edge = ForeignKeyEdge(
        object_id="dera:foreign_key:e1",
        native_name="e1",
        source_table_id="dera:table:nonexistent",
        referenced_table_id=node.object_id,
        source_table_name="nonexistent",
        referenced_table_name="valid",
        column_pairs=(pair,),
        provenance=prov,
    )

    with pytest.raises(GraphValidationError):
        validate_foreign_key_graph(nodes=(node,), edges=(edge,), mode=ValidationMode.STRICT)


def test_builder_rejects_duplicate_node_ids():
    prov = make_graph_provenance()
    builder = ForeignKeyGraphBuilder(
        database_id="dera:database:db", database_name="db", engine="postgresql"
    )
    node1 = TableNode(object_id="dera:table:duplicate", native_name="t1", provenance=prov)
    node2 = TableNode(object_id="dera:table:duplicate", native_name="t2", provenance=prov)

    builder.add_node(node1)
    with pytest.raises(GraphBuilderError, match="Duplicate table node ObjectId"):
        builder.add_node(node2)
