"""DERA Phase 8.3 — Graph Helpers Unit Tests.

Validates graph resolution, dependency resolution, reverse reachability traversal,
and parallel edge grouping helpers.
"""

from __future__ import annotations

from dera.diagnostics.context import DiagnosticContext
from dera.diagnostics.rules.shared.graph_helpers import (
    compute_reverse_reachability,
    get_table_node_map,
    group_parallel_edges,
    resolve_dependencies,
    resolve_graph,
)
from dera.metadata.enums import MetadataCompleteness
from dera.metadata.provenance import MetadataProvenance
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge, ResolutionStatus
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.graph.nodes import TableNode


def _make_table_node(
    name: str,
    namespace: str = "public",
    pk_cols: tuple[str, ...] = ("id",),
) -> TableNode:
    oid = f"node_{namespace}_{name}"
    prov = MetadataProvenance(source_engine="postgresql", native_identifier=name)
    return TableNode(
        object_id=oid,
        native_name=name,
        namespace_name=namespace,
        column_count=5,
        primary_key_columns=pk_cols,
        completeness=MetadataCompleteness.COMPLETE,
        provenance=prov,
    )


def _make_fk_edge(
    source_node: TableNode,
    ref_node: TableNode | None,
    name: str,
    column_pairs: tuple[tuple[str, str], ...] = (("parent_id", "id"),),
    is_cross_namespace: bool = False,
    is_self: bool = False,
) -> ForeignKeyEdge:
    oid = f"edge_{name}"
    prov = MetadataProvenance(source_engine="postgresql", native_identifier=name)
    mappings = tuple(
        ColumnPairMapping(
            source_column_name=src,
            referenced_column_name=ref,
            ordinal_position=idx + 1,
        )
        for idx, (src, ref) in enumerate(column_pairs)
    )
    return ForeignKeyEdge(
        object_id=oid,
        native_name=name,
        source_table_id=source_node.object_id,
        referenced_table_id=ref_node.object_id if ref_node else None,
        source_namespace=source_node.namespace_name,
        source_table_name=source_node.native_name,
        referenced_namespace=ref_node.namespace_name if ref_node else "public",
        referenced_table_name=ref_node.native_name if ref_node else "missing_table",
        column_pairs=mappings,
        is_composite=len(mappings) > 1,
        is_self_referencing=is_self,
        is_cross_namespace=is_cross_namespace,
        resolution_status=ResolutionStatus.RESOLVED if ref_node else ResolutionStatus.MISSING,
        provenance=prov,
    )


def _build_graph(
    nodes: tuple[TableNode, ...], edges: tuple[ForeignKeyEdge, ...]
) -> ForeignKeyGraph:
    from dera.reverse_engineering.graph.capabilities import GraphCapabilityProfile

    prov = MetadataProvenance(source_engine="postgresql", native_identifier="test_db")
    cap = GraphCapabilityProfile(
        engine="postgresql",
        supports_foreign_keys=True,
        supports_composite_fks=True,
        supports_deferrable_fks=True,
        supports_cross_schema_fks=True,
    )
    return ForeignKeyGraph(
        contract_version="1.0.0",
        database_id="db_main",
        database_name="test_db",
        engine="postgresql",
        workspace_id=None,
        completeness=MetadataCompleteness.COMPLETE,
        nodes=nodes,
        edges=edges,
        unresolved_references=(),
        capability_profile=cap,
        provenance=prov,
    )


def test_get_table_node_map():
    t1 = _make_table_node("users")
    t2 = _make_table_node("orders")
    graph = _build_graph((t1, t2), ())

    node_map = get_table_node_map(graph)
    assert len(node_map) == 2
    assert node_map[t1.object_id] == t1
    assert node_map[t2.object_id] == t2


def test_group_parallel_edges():
    t_child = _make_table_node("orders")
    t_parent = _make_table_node("users")
    e1 = _make_fk_edge(t_child, t_parent, "fk_orders_billing_user", (("billing_user_id", "id"),))
    e2 = _make_fk_edge(t_child, t_parent, "fk_orders_shipping_user", (("shipping_user_id", "id"),))

    graph = _build_graph((t_child, t_parent), (e1, e2))
    grouped = group_parallel_edges(graph.edges)

    key = (t_child.object_id, t_parent.object_id)
    assert key in grouped
    assert len(grouped[key]) == 2
    assert grouped[key][0].native_name == "fk_orders_billing_user"
    assert grouped[key][1].native_name == "fk_orders_shipping_user"


def test_compute_reverse_reachability_dag():
    # Chain: C -> B -> A (C references B, B references A)
    # Downstream dependents of A: {B, C}
    t_a = _make_table_node("a")
    t_b = _make_table_node("b")
    t_c = _make_table_node("c")

    # Parent -> child reverse adjacency
    dependent_adj = {
        t_a.object_id: (t_b.object_id,),
        t_b.object_id: (t_c.object_id,),
    }

    dependents, max_depth = compute_reverse_reachability(t_a.object_id, dependent_adj, max_depth=10)

    assert set(dependents) == {t_b.object_id, t_c.object_id}
    assert max_depth == 2


def test_compute_reverse_reachability_bounded_depth():
    # Chain: D -> C -> B -> A
    t_a = _make_table_node("a")
    t_b = _make_table_node("b")
    t_c = _make_table_node("c")
    t_d = _make_table_node("d")

    dependent_adj = {
        t_a.object_id: (t_b.object_id,),
        t_b.object_id: (t_c.object_id,),
        t_c.object_id: (t_d.object_id,),
    }

    # At max_depth=1, only B is discovered
    depth_1_dependents, d1 = compute_reverse_reachability(t_a.object_id, dependent_adj, max_depth=1)
    assert depth_1_dependents == (t_b.object_id,)
    assert d1 == 1

    # At max_depth=2, B and C are discovered
    depth_2_dependents, d2 = compute_reverse_reachability(t_a.object_id, dependent_adj, max_depth=2)
    assert set(depth_2_dependents) == {t_b.object_id, t_c.object_id}
    assert d2 == 2


def test_resolve_graph_and_dependencies():
    t_a = _make_table_node("a")
    t_b = _make_table_node("b")
    e1 = _make_fk_edge(t_b, t_a, "fk_b_a")
    graph = _build_graph((t_a, t_b), (e1,))

    ctx = DiagnosticContext(graph=graph)
    resolved_g = resolve_graph(ctx)
    assert resolved_g is not None
    assert len(resolved_g.nodes) == 2

    resolved_deps = resolve_dependencies(ctx)
    assert resolved_deps is not None
    assert resolved_deps.node_count == 2
    assert resolved_deps.is_dag is True
