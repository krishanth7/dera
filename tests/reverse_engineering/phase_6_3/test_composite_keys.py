"""Tests for composite foreign key sequence preservation and length validation."""

from __future__ import annotations

from dera.metadata.enums import ObjectKind
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.models import (
    CanonicalDatabase,
    CanonicalForeignKey,
    CanonicalNamespace,
    CanonicalTable,
)
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.models import UnresolvedReason

from tests.reverse_engineering.phase_6_3.fixtures import (
    make_composite_fk_schema,
    make_graph_provenance,
    make_test_column,
)


def test_composite_foreign_key_column_pair_ordering():
    """Verify multi-column foreign key mappings preserve exact declared ordinal sequence."""
    db = make_composite_fk_schema()
    graph = ForeignKeyGraphBuilder.from_canonical(db)

    emp = graph.get_node_by_name("employees")
    br = graph.get_node_by_name("branches")
    assert emp is not None
    assert br is not None

    edges = graph.outgoing(emp.object_id)
    assert len(edges) == 1
    edge = edges[0]

    assert edge.is_composite is True
    assert len(edge.column_pairs) == 2

    p1, p2 = edge.column_pairs
    assert p1.ordinal_position == 1
    assert p1.source_column_name == "tenant_id"
    assert p1.referenced_column_name == "tenant_id"

    assert p2.ordinal_position == 2
    assert p2.source_column_name == "branch_id"
    assert p2.referenced_column_name == "branch_id"

    assert edge.source_columns == ("tenant_id", "branch_id")
    assert edge.referenced_columns == ("tenant_id", "branch_id")


def test_mismatched_composite_key_lengths_reported_as_unresolved():
    """Verify mismatched composite foreign key column counts are auditable unresolved references."""
    prov = make_graph_provenance()
    db_id = compute_stable_object_id("postgresql", ObjectKind.DATABASE, "mismatch_db")
    ns_id = compute_stable_object_id("postgresql", ObjectKind.NAMESPACE, "public", parent_id=db_id)

    p_id = compute_stable_object_id("postgresql", ObjectKind.TABLE, "parent", parent_id=ns_id)
    p_table = CanonicalTable(
        id=p_id, namespace_id=ns_id, name="parent", schema_name="public",
        columns=(make_test_column(p_id, "p1", 1),),
        provenance=prov,
    )

    c_id = compute_stable_object_id("postgresql", ObjectKind.TABLE, "child", parent_id=ns_id)
    fk = CanonicalForeignKey(
        id=compute_stable_object_id("postgresql", ObjectKind.FOREIGN_KEY, "fk_mismatch", parent_id=c_id),
        table_id=c_id,
        name="fk_mismatch",
        column_names=("c1", "c2"),
        referenced_table_id=p_id,
        referenced_schema_name="public",
        referenced_table_name="parent",
        referenced_column_names=("p1",),
        provenance=prov,
    )
    c_table = CanonicalTable(
        id=c_id, namespace_id=ns_id, name="child", schema_name="public",
        columns=(make_test_column(c_id, "c1", 1), make_test_column(c_id, "c2", 2)),
        foreign_keys=(fk,),
        provenance=prov,
    )

    db = CanonicalDatabase(
        id=db_id, name="mismatch_db", engine="postgresql",
        namespaces=(CanonicalNamespace(id=ns_id, name="public", tables=(p_table, c_table), provenance=prov),),
        provenance=prov,
    )

    graph = ForeignKeyGraphBuilder.from_canonical(db)
    assert len(graph.unresolved_references) == 1
    unres = graph.unresolved_references[0]
    assert unres.reason == UnresolvedReason.INVALID_METADATA
    assert "Mismatched composite foreign key column counts" in unres.details
