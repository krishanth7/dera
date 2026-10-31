"""Tests for Phase 8.3 Relationship Diagnostic Rules.

Covers DERA-REL-001 (Graph Integrity), DERA-REL-002 (Unresolved Targets),
DERA-REL-003 (Composite Mappings), and DERA-REL-004 (Cross-Namespace Dependencies).
"""

from __future__ import annotations

from dera.diagnostics.context import DiagnosticContext
from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
)
from dera.diagnostics.rules.relationships.composite_mappings import (
    CompositeForeignKeyMappingRule,
)
from dera.diagnostics.rules.relationships.cross_namespace import (
    CrossNamespaceDependenciesRule,
)
from dera.diagnostics.rules.relationships.graph_integrity import (
    RelationshipGraphIntegrityRule,
)
from dera.diagnostics.rules.relationships.unresolved_targets import (
    UnresolvedRelationshipTargetsRule,
)
from dera.metadata.enums import MetadataCompleteness
from dera.metadata.provenance import MetadataProvenance
from dera.reverse_engineering.graph.capabilities import GraphCapabilityProfile
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge
from dera.reverse_engineering.graph.models import (
    ForeignKeyGraph,
    UnresolvedReason,
    UnresolvedReference,
)
from dera.reverse_engineering.graph.nodes import TableNode
from dera.reverse_engineering.references import ResolutionStatus


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
    column_pairs: tuple[tuple[str, str], ...],
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


def _make_graph(
    nodes: tuple[TableNode, ...],
    edges: tuple[ForeignKeyEdge, ...] = (),
    unresolved: tuple[UnresolvedReference, ...] = (),
) -> ForeignKeyGraph:
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
        database_id="db_test",
        database_name="test_db",
        engine="postgresql",
        nodes=nodes,
        edges=edges,
        unresolved_references=unresolved,
        capability_profile=cap,
        provenance=prov,
    )


# ---------------------------------------------------------------------------
# DERA-REL-001: Relationship Graph Integrity Tests
# ---------------------------------------------------------------------------


def test_rel_001_valid_graph_passes():
    t_parent = _make_table_node("users")
    t_child = _make_table_node("orders")
    edge = _make_fk_edge(t_child, t_parent, "fk_orders_users", (("user_id", "id"),))
    graph = _make_graph((t_parent, t_child), (edge,))

    rule = RelationshipGraphIntegrityRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.PASS
    assert len(res.findings) == 0


def test_rel_001_dangling_source_node():
    t_parent = _make_table_node("users")
    t_child = _make_table_node("orders")
    edge = _make_fk_edge(t_child, t_parent, "fk_orders_users", (("user_id", "id"),))
    # Register only parent in graph nodes, omitting child
    graph = _make_graph((t_parent,), (edge,))

    rule = RelationshipGraphIntegrityRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert any("Dangling Source Node" in f.title for f in res.findings)


def test_rel_001_dangling_target_node():
    t_parent = _make_table_node("users")
    t_child = _make_table_node("orders")
    edge = _make_fk_edge(t_child, t_parent, "fk_orders_users", (("user_id", "id"),))
    # Register only child in graph nodes, omitting parent
    graph = _make_graph((t_child,), (edge,))

    rule = RelationshipGraphIntegrityRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert any("Dangling Target Node" in f.title for f in res.findings)


def test_rel_001_empty_column_mapping():
    t_parent = _make_table_node("users")
    t_child = _make_table_node("orders")
    # Construct edge with zero column mappings
    edge = ForeignKeyEdge(
        object_id="edge_corrupt",
        native_name="fk_corrupt",
        source_table_id=t_child.object_id,
        referenced_table_id=t_parent.object_id,
        source_namespace="public",
        source_table_name="orders",
        referenced_namespace="public",
        referenced_table_name="users",
        column_pairs=(),
        provenance=MetadataProvenance(source_engine="postgresql", native_identifier="fk_corrupt"),
    )
    graph = _make_graph((t_parent, t_child), (edge,))

    rule = RelationshipGraphIntegrityRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert any("Empty Column Mapping" in f.title for f in res.findings)


# ---------------------------------------------------------------------------
# DERA-REL-002: Unresolved Relationship Targets Tests
# ---------------------------------------------------------------------------


def test_rel_002_clean_graph_passes():
    t_parent = _make_table_node("users")
    t_child = _make_table_node("orders")
    edge = _make_fk_edge(t_child, t_parent, "fk_orders_users", (("user_id", "id"),))
    graph = _make_graph((t_parent, t_child), (edge,))

    rule = UnresolvedRelationshipTargetsRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.PASS
    assert len(res.findings) == 0


def test_rel_002_unresolved_target_detected():
    t_child = _make_table_node("payments")
    unres = UnresolvedReference(
        foreign_key_id="fk_payments_gateway",
        native_name="fk_payments_gateway",
        source_table_id=t_child.object_id,
        source_table_name="payments",
        source_namespace="public",
        referenced_table_name="gateways",
        referenced_namespace="billing",
        declared_source_columns=("gateway_id",),
        declared_referenced_columns=("id",),
        reason=UnresolvedReason.REFERENCED_TABLE_NOT_FOUND,
        details="Table 'billing.gateways' not found in schema.",
        provenance=MetadataProvenance(
            source_engine="postgresql", native_identifier="fk_payments_gateway"
        ),
    )
    graph = _make_graph((t_child,), (), (unres,))

    rule = UnresolvedRelationshipTargetsRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    assert res.findings[0].severity == DiagnosticSeverity.MEDIUM
    assert "Unresolved Foreign Key Relationship Target" in res.findings[0].title


def test_rel_002_restricted_metadata_low_severity():
    t_child = _make_table_node("audit_log")
    unres = UnresolvedReference(
        foreign_key_id="fk_audit_admin",
        native_name="fk_audit_admin",
        source_table_id=t_child.object_id,
        source_table_name="audit_log",
        source_namespace="public",
        referenced_table_name="admins",
        referenced_namespace="security",
        declared_source_columns=("admin_id",),
        declared_referenced_columns=("id",),
        reason=UnresolvedReason.METADATA_RESTRICTED,
        details="Access to namespace 'security' restricted by catalog permissions.",
        provenance=MetadataProvenance(
            source_engine="postgresql", native_identifier="fk_audit_admin"
        ),
    )
    graph = _make_graph((t_child,), (), (unres,))

    rule = UnresolvedRelationshipTargetsRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert res.findings[0].severity == DiagnosticSeverity.LOW


# ---------------------------------------------------------------------------
# DERA-REL-003: Composite Foreign Key Mapping Integrity Tests
# ---------------------------------------------------------------------------


def test_rel_003_valid_composite_passes():
    t_parent = _make_table_node("parent_items", pk_cols=("tenant_id", "item_id"))
    t_child = _make_table_node("child_items")
    edge = _make_fk_edge(
        t_child,
        t_parent,
        "fk_child_parent",
        (("tenant_id", "tenant_id"), ("item_id", "item_id")),
    )
    graph = _make_graph((t_parent, t_child), (edge,))

    rule = CompositeForeignKeyMappingRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.PASS


def test_rel_003_non_contiguous_ordinals():
    t_parent = _make_table_node("parent_items")
    t_child = _make_table_node("child_items")
    # Create non-contiguous ordinals: 1, 3
    p1 = ColumnPairMapping(source_column_name="c1", referenced_column_name="p1", ordinal_position=1)
    p2 = ColumnPairMapping(source_column_name="c2", referenced_column_name="p2", ordinal_position=3)
    edge = ForeignKeyEdge(
        object_id="edge_bad_ordinals",
        native_name="fk_bad_ordinals",
        source_table_id=t_child.object_id,
        referenced_table_id=t_parent.object_id,
        source_namespace="public",
        source_table_name="child_items",
        referenced_namespace="public",
        referenced_table_name="parent_items",
        column_pairs=(p1, p2),
        is_composite=True,
        provenance=MetadataProvenance(
            source_engine="postgresql", native_identifier="fk_bad_ordinals"
        ),
    )
    graph = _make_graph((t_parent, t_child), (edge,))

    rule = CompositeForeignKeyMappingRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert any("Non-Contiguous Composite Column Ordinals" in f.title for f in res.findings)


def test_rel_003_duplicate_source_column():
    t_parent = _make_table_node("parent_items")
    t_child = _make_table_node("child_items")
    # c1 mapped twice to different parent columns
    p1 = ColumnPairMapping(source_column_name="c1", referenced_column_name="p1", ordinal_position=1)
    p2 = ColumnPairMapping(source_column_name="c1", referenced_column_name="p2", ordinal_position=2)
    edge = ForeignKeyEdge(
        object_id="edge_dup_source",
        native_name="fk_dup_source",
        source_table_id=t_child.object_id,
        referenced_table_id=t_parent.object_id,
        source_namespace="public",
        source_table_name="child_items",
        referenced_namespace="public",
        referenced_table_name="parent_items",
        column_pairs=(p1, p2),
        is_composite=True,
        provenance=MetadataProvenance(
            source_engine="postgresql", native_identifier="fk_dup_source"
        ),
    )
    graph = _make_graph((t_parent, t_child), (edge,))

    rule = CompositeForeignKeyMappingRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert any("Duplicate Source Column" in f.title for f in res.findings)


# ---------------------------------------------------------------------------
# DERA-REL-004: Cross-Namespace Dependencies Tests
# ---------------------------------------------------------------------------


def test_rel_004_intra_namespace_passes():
    t_parent = _make_table_node("users", namespace="public")
    t_child = _make_table_node("orders", namespace="public")
    edge = _make_fk_edge(t_child, t_parent, "fk_orders_users", (("user_id", "id"),))
    graph = _make_graph((t_parent, t_child), (edge,))

    rule = CrossNamespaceDependenciesRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.PASS
    assert len(res.findings) == 0


def test_rel_004_cross_namespace_detected():
    t_parent = _make_table_node("accounts", namespace="auth")
    t_child = _make_table_node("events", namespace="analytics")
    edge = _make_fk_edge(
        t_child,
        t_parent,
        "fk_events_accounts",
        (("account_id", "id"),),
        is_cross_namespace=True,
    )
    graph = _make_graph((t_parent, t_child), (edge,))

    rule = CrossNamespaceDependenciesRule()
    ctx = DiagnosticContext(graph=graph)
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    assert res.findings[0].severity == DiagnosticSeverity.INFORMATIONAL
    assert "Cross-Namespace Foreign Key Dependency" in res.findings[0].title
    assert "analytics.events" in res.findings[0].description
    assert "auth.accounts" in res.findings[0].description
