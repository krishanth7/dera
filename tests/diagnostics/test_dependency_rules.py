"""Tests for Phase 8.3 Dependency Diagnostic Rules.

Covers DERA-DEP-001 (Cyclic Dependencies & SCCs), DERA-DEP-002 (Dependency Depth),
DERA-DEP-003 (Dependency Concentration), and DERA-DEP-004 (Structural Impact Radius).
"""

from __future__ import annotations

from dera.diagnostics.context import DiagnosticContext, DiagnosticEngineConfig
from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
)
from dera.diagnostics.rules.relationships.cyclic_dependencies import (
    CyclicDependenciesRule,
)
from dera.diagnostics.rules.relationships.dependency_concentration import (
    DependencyConcentrationRule,
)
from dera.diagnostics.rules.relationships.dependency_depth import (
    DependencyDepthRule,
)
from dera.diagnostics.rules.relationships.structural_impact import (
    StructuralImpactRadiusRule,
)
from dera.metadata.enums import MetadataCompleteness
from dera.metadata.provenance import MetadataProvenance
from dera.reverse_engineering.graph.capabilities import GraphCapabilityProfile
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.graph.nodes import TableNode
from dera.reverse_engineering.references import ResolutionStatus


def _make_table_node(name: str, namespace: str = "public") -> TableNode:
    oid = f"node_{namespace}_{name}"
    prov = MetadataProvenance(source_engine="postgresql", native_identifier=name)
    return TableNode(
        object_id=oid,
        native_name=name,
        namespace_name=namespace,
        column_count=5,
        primary_key_columns=("id",),
        completeness=MetadataCompleteness.COMPLETE,
        provenance=prov,
    )


def _make_fk_edge(
    source_node: TableNode,
    ref_node: TableNode,
    name: str,
    is_self: bool = False,
) -> ForeignKeyEdge:
    oid = f"edge_{name}"
    prov = MetadataProvenance(source_engine="postgresql", native_identifier=name)
    mapping = ColumnPairMapping(
        source_column_name="ref_id",
        referenced_column_name="id",
        ordinal_position=1,
    )
    return ForeignKeyEdge(
        object_id=oid,
        native_name=name,
        source_table_id=source_node.object_id,
        referenced_table_id=ref_node.object_id,
        source_namespace=source_node.namespace_name,
        source_table_name=source_node.native_name,
        referenced_namespace=ref_node.namespace_name,
        referenced_table_name=ref_node.native_name,
        column_pairs=(mapping,),
        is_composite=False,
        is_self_referencing=is_self,
        is_cross_namespace=source_node.namespace_name != ref_node.namespace_name,
        resolution_status=ResolutionStatus.RESOLVED,
        provenance=prov,
    )


def _build_graph(
    nodes: tuple[TableNode, ...], edges: tuple[ForeignKeyEdge, ...] = ()
) -> ForeignKeyGraph:
    prov = MetadataProvenance(source_engine="postgresql", native_identifier="test_db")
    cap = GraphCapabilityProfile(
        engine="postgresql",
        supports_foreign_keys=True,
        supports_composite_fks=True,
    )
    return ForeignKeyGraph(
        contract_version="1.0.0",
        database_id="db_test",
        database_name="test_db",
        engine="postgresql",
        nodes=nodes,
        edges=edges,
        capability_profile=cap,
        provenance=prov,
    )


# ---------------------------------------------------------------------------
# DERA-DEP-001: Cyclic Dependencies Tests
# ---------------------------------------------------------------------------


def test_dep_001_acyclic_graph_passes():
    t_users = _make_table_node("users")
    t_orders = _make_table_node("orders")
    t_items = _make_table_node("order_items")

    e1 = _make_fk_edge(t_items, t_orders, "fk_items_orders")
    e2 = _make_fk_edge(t_orders, t_users, "fk_orders_users")

    graph = _build_graph((t_users, t_orders, t_items), (e1, e2))
    rule = CyclicDependenciesRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.PASS
    assert len(res.findings) == 0


def test_dep_001_self_referencing_loop():
    t_categories = _make_table_node("categories")
    e_self = _make_fk_edge(t_categories, t_categories, "fk_categories_parent", is_self=True)

    graph = _build_graph((t_categories,), (e_self,))
    rule = CyclicDependenciesRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    assert res.findings[0].severity == DiagnosticSeverity.LOW
    assert "Self-Referencing" in res.findings[0].title


def test_dep_001_two_node_circular_dependency():
    t_a = _make_table_node("table_a")
    t_b = _make_table_node("table_b")

    # Cycle: A -> B and B -> A
    e1 = _make_fk_edge(t_a, t_b, "fk_a_b")
    e2 = _make_fk_edge(t_b, t_a, "fk_b_a")

    graph = _build_graph((t_a, t_b), (e1, e2))
    rule = CyclicDependenciesRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    assert res.findings[0].severity == DiagnosticSeverity.MEDIUM
    assert "table_a" in res.findings[0].description
    assert "table_b" in res.findings[0].description


# ---------------------------------------------------------------------------
# DERA-DEP-002: Dependency Depth Tests
# ---------------------------------------------------------------------------


def test_dep_002_shallow_graph_passes():
    t_a = _make_table_node("a")
    t_b = _make_table_node("b")
    t_c = _make_table_node("c")

    e1 = _make_fk_edge(t_b, t_a, "fk_b_a")
    e2 = _make_fk_edge(t_c, t_b, "fk_c_b")

    graph = _build_graph((t_a, t_b, t_c), (e1, e2))
    rule = DependencyDepthRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.PASS


def test_dep_002_deep_chain_detected():
    # Construct a chain of 6 levels: T6 -> T5 -> T4 -> T3 -> T2 -> T1
    nodes = [_make_table_node(f"t{i}") for i in range(1, 7)]
    edges = []
    for i in range(1, 6):
        edges.append(_make_fk_edge(nodes[i], nodes[i - 1], f"fk_{i}_{i - 1}"))

    graph = _build_graph(tuple(nodes), tuple(edges))
    rule = DependencyDepthRule()

    # Default threshold is 5; node t6 (index 5) has depth 5
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert any("Deep Dependency Chain" in f.title for f in res.findings)


def test_dep_002_configured_depth_threshold():
    t_a = _make_table_node("a")
    t_b = _make_table_node("b")
    t_c = _make_table_node("c")
    e1 = _make_fk_edge(t_b, t_a, "fk_b_a")
    e2 = _make_fk_edge(t_c, t_b, "fk_c_b")

    graph = _build_graph((t_a, t_b, t_c), (e1, e2))
    rule = DependencyDepthRule()

    # Set threshold to 2; node c has depth 2
    cfg = DiagnosticEngineConfig(rule_thresholds={"max_dependency_depth": 2})
    ctx = DiagnosticContext(graph=graph, config=cfg)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert any(f.object_id == t_c.object_id for f in res.findings)


# ---------------------------------------------------------------------------
# DERA-DEP-003: High Dependency Concentration Tests
# ---------------------------------------------------------------------------


def test_dep_003_high_fan_in_hub():
    # Root table referenced by 9 child tables
    t_root = _make_table_node("core_user")
    children = [_make_table_node(f"service_{i}") for i in range(9)]
    edges = [_make_fk_edge(c, t_root, f"fk_service_{i}_user") for i, c in enumerate(children)]

    graph = _build_graph((t_root, *children), tuple(edges))
    rule = DependencyConcentrationRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    hub_findings = [f for f in res.findings if "Fan-In Hub" in f.title]
    assert len(hub_findings) == 1
    assert hub_findings[0].object_id == t_root.object_id
    assert hub_findings[0].severity == DiagnosticSeverity.LOW

    # Twice threshold: 16 child tables
    extra_children = [_make_table_node(f"extra_service_{i}") for i in range(7)]
    all_children = children + extra_children
    edges_2x = [_make_fk_edge(c, t_root, f"fk_all_service_{i}") for i, c in enumerate(all_children)]
    graph_2x = _build_graph((t_root, *all_children), tuple(edges_2x))
    res_2x = rule.evaluate(DiagnosticContext(graph=graph_2x))
    hub_findings_2x = [f for f in res_2x.findings if "Fan-In Hub" in f.title]
    assert len(hub_findings_2x) == 1
    assert hub_findings_2x[0].severity == DiagnosticSeverity.MEDIUM


def test_dep_003_high_fan_out_consumer():
    # Consumer table referencing 9 parent tables
    t_consumer = _make_table_node("reporting_fact")
    parents = [_make_table_node(f"dimension_{i}") for i in range(9)]
    edges = [_make_fk_edge(t_consumer, p, f"fk_report_{i}") for i, p in enumerate(parents)]

    graph = _build_graph((t_consumer, *parents), tuple(edges))
    rule = DependencyConcentrationRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    consumer_findings = [f for f in res.findings if "Fan-Out Consumer" in f.title]
    assert len(consumer_findings) == 1
    assert consumer_findings[0].object_id == t_consumer.object_id
    assert consumer_findings[0].severity == DiagnosticSeverity.LOW

    # Twice threshold: 16 parent tables
    extra_parents = [_make_table_node(f"extra_dim_{i}") for i in range(7)]
    all_parents = parents + extra_parents
    edges_2x = [
        _make_fk_edge(t_consumer, p, f"fk_all_report_{i}") for i, p in enumerate(all_parents)
    ]
    graph_2x = _build_graph((t_consumer, *all_parents), tuple(edges_2x))
    res_2x = rule.evaluate(DiagnosticContext(graph=graph_2x))
    consumer_findings_2x = [f for f in res_2x.findings if "Fan-Out Consumer" in f.title]
    assert len(consumer_findings_2x) == 1
    assert consumer_findings_2x[0].severity == DiagnosticSeverity.MEDIUM


# ---------------------------------------------------------------------------
# DERA-DEP-004: Structural Impact Radius Tests
# ---------------------------------------------------------------------------


def test_dep_004_structural_impact_radius():
    # Root node with 11 downstream dependents
    t_root = _make_table_node("org_root")
    children = [_make_table_node(f"org_child_{i}") for i in range(11)]
    edges = [_make_fk_edge(c, t_root, f"fk_org_{i}") for i, c in enumerate(children)]

    graph = _build_graph((t_root, *children), tuple(edges))
    rule = StructuralImpactRadiusRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    impact_findings = [f for f in res.findings if "High Structural Impact Radius" in f.title]
    assert len(impact_findings) == 1
    assert impact_findings[0].object_id == t_root.object_id
    assert impact_findings[0].severity == DiagnosticSeverity.LOW

    # Twice threshold: 20 dependents
    extra_children = [_make_table_node(f"extra_child_{i}") for i in range(9)]
    all_children = children + extra_children
    edges_2x = [_make_fk_edge(c, t_root, f"fk_all_org_{i}") for i, c in enumerate(all_children)]
    graph_2x = _build_graph((t_root, *all_children), tuple(edges_2x))
    res_2x = rule.evaluate(DiagnosticContext(graph=graph_2x))
    impact_findings_2x = [f for f in res_2x.findings if "High Structural Impact Radius" in f.title]
    assert len(impact_findings_2x) == 1
    assert impact_findings_2x[0].severity == DiagnosticSeverity.MEDIUM
