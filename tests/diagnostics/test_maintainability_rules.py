"""Unit and integration tests for Phase 8.4 Maintainability Diagnostic Rules.

Covers:
- DERA-MNT-001: Excessive Table Width (Wide Table Pattern)
- DERA-MNT-002: High Column Nullability Ratio
- DERA-MNT-003: Identifier Naming Convention Inconsistency
- DERA-MNT-004: Reserved Word Identifier Usage
- DERA-MNT-005: Namespace Object Imbalance & Monolithic Schema
- DERA-MNT-006: High Relationship Structural Coupling
- DERA-MNT-007: Complex Dependency Topology
- DERA-MNT-008: Excessive Text/Binary LOB Column Concentration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dera.diagnostics.context import DiagnosticContext, DiagnosticEngineConfig
from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
)
from dera.diagnostics.rules.maintainability import (
    ColumnNullabilityRule,
    ComplexDependencyTopologyRule,
    LobConcentrationRule,
    NamespaceImbalanceRule,
    NamingConsistencyRule,
    ReservedWordUsageRule,
    StructuralCouplingRule,
    TableWidthRule,
)
from dera.metadata.enums import MetadataCompleteness
from dera.metadata.provenance import MetadataProvenance
from dera.reverse_engineering.graph.capabilities import GraphCapabilityProfile
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.graph.nodes import TableNode
from dera.reverse_engineering.references import ResolutionStatus

# ---------------------------------------------------------------------------
# Lightweight test fixtures
# ---------------------------------------------------------------------------


@dataclass
class MockColumn:
    name: str
    id: str = "col_id"
    is_nullable: bool = True
    default_expression: str | None = None
    is_identity: bool = False
    is_generated: bool = False
    native_data_type: str = "varchar(255)"
    canonical_type: str = "VARCHAR"


@dataclass
class MockTable:
    name: str
    id: str = "tbl_id"
    columns: tuple[MockColumn, ...] = ()
    indexes: tuple = ()
    foreign_keys: tuple = ()
    unique_constraints: tuple = ()
    check_constraints: tuple = ()
    primary_key: Any = None
    schema_name: str | None = "public"


@dataclass
class MockNamespace:
    name: str
    tables: tuple[MockTable, ...] = ()
    views: tuple = ()


@dataclass
class MockDatabase:
    name: str = "test_db"
    namespaces: tuple[MockNamespace, ...] = ()

    def all_tables(self) -> tuple[MockTable, ...]:
        tbls = []
        for ns in self.namespaces:
            tbls.extend(ns.tables)
        return tuple(tbls)


@dataclass
class MockSchemaRepresentation:
    database: MockDatabase = field(default_factory=MockDatabase)

    @property
    def tables(self) -> tuple[MockTable, ...]:
        return self.database.all_tables()

    @property
    def namespaces(self) -> tuple[MockNamespace, ...]:
        return self.database.namespaces


def _build_context(
    tables: tuple[MockTable, ...],
    namespaces: tuple[MockNamespace, ...] | None = None,
    dialect: str = "postgresql",
    config: DiagnosticEngineConfig | None = None,
) -> DiagnosticContext:
    if namespaces is None:
        namespaces = (MockNamespace(name="public", tables=tables),)
    db = MockDatabase(name="test_db", namespaces=namespaces)
    schema = MockSchemaRepresentation(database=db)
    return DiagnosticContext(
        schema=schema,
        source_engine=dialect,
        config=config or DiagnosticEngineConfig(),
    )


# ---------------------------------------------------------------------------
# DERA-MNT-001: Table Width Tests
# ---------------------------------------------------------------------------


def test_mnt_001_normal_table_passes():
    cols = tuple(MockColumn(name=f"col_{i}") for i in range(15))
    tbl = MockTable(name="orders", columns=cols)
    ctx = _build_context((tbl,))
    rule = TableWidthRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.PASS
    assert len(res.findings) == 0


def test_mnt_001_wide_table_findings():
    # 55 columns triggers REVIEW (threshold 50) -> LOW severity
    cols = tuple(MockColumn(name=f"col_{i}") for i in range(55))
    tbl = MockTable(name="wide_table", columns=cols)
    ctx = _build_context((tbl,))
    rule = TableWidthRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    f = res.findings[0]
    assert f.rule_id == "DERA-MNT-001"
    assert f.severity == DiagnosticSeverity.LOW
    assert "Wide Table" in f.title
    assert f.evidence[0].observed_value == 55


def test_mnt_001_elevated_wide_table_findings():
    # 105 columns triggers ELEVATED (threshold 100) -> MEDIUM severity
    cols = tuple(MockColumn(name=f"col_{i}") for i in range(105))
    tbl = MockTable(name="huge_table", columns=cols)
    ctx = _build_context((tbl,))
    rule = TableWidthRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    assert res.findings[0].severity == DiagnosticSeverity.MEDIUM


# ---------------------------------------------------------------------------
# DERA-MNT-002: Column Nullability Ratio Tests
# ---------------------------------------------------------------------------


def test_mnt_002_low_nullability_passes():
    cols = (
        MockColumn(name="c1", is_nullable=False),
        MockColumn(name="c2", is_nullable=False),
        MockColumn(name="c3", is_nullable=False),
        MockColumn(name="c4", is_nullable=False),
        MockColumn(name="c5", is_nullable=True),
    )
    tbl = MockTable(name="users", columns=cols)
    ctx = _build_context((tbl,))
    rule = ColumnNullabilityRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.PASS
    assert len(res.findings) == 0


def test_mnt_002_high_nullability_detection():
    # 6 nullable out of 8 (75%) -> triggers INFORMATIONAL severity
    cols = tuple(
        MockColumn(name=f"c_{i}", is_nullable=(i >= 2)) for i in range(8)
    )  # 6 nullable, 2 not null
    tbl = MockTable(name="sparse_data", columns=cols)
    ctx = _build_context((tbl,))
    rule = ColumnNullabilityRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    f = res.findings[0]
    assert f.rule_id == "DERA-MNT-002"
    assert f.severity == DiagnosticSeverity.LOW
    assert f.evidence[0].observed_value == 0.75


def test_mnt_002_critical_nullability_detection():
    # 9 nullable out of 10 (90%) -> triggers LOW severity (threshold 0.85)
    cols = tuple(MockColumn(name=f"c_{i}", is_nullable=(i >= 1)) for i in range(10))
    tbl = MockTable(name="very_sparse_data", columns=cols)
    ctx = _build_context((tbl,))
    rule = ColumnNullabilityRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    assert res.findings[0].severity == DiagnosticSeverity.LOW


# ---------------------------------------------------------------------------
# DERA-MNT-003: Naming Consistency Tests
# ---------------------------------------------------------------------------


def test_mnt_003_snake_case_passes():
    cols = (
        MockColumn(name="order_id"),
        MockColumn(name="customer_id"),
        MockColumn(name="total_amount"),
    )
    tbl = MockTable(name="order_items", columns=cols)
    ctx = _build_context((tbl,))
    rule = NamingConsistencyRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.PASS
    assert len(res.findings) == 0


def test_mnt_003_mixed_casing_finding():
    cols = (
        MockColumn(name="order_id"),
        MockColumn(name="customerName"),
        MockColumn(name="TotalAmount"),
    )
    tbl = MockTable(name="orders_data", columns=cols)
    ctx = _build_context((tbl,))
    rule = NamingConsistencyRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 2  # customerName and TotalAmount
    assert all(f.severity == DiagnosticSeverity.INFORMATIONAL for f in res.findings)
    assert any("customerName" in f.title for f in res.findings)
    assert any("TotalAmount" in f.title for f in res.findings)


def test_mnt_003_table_name_deviation():
    cols = (MockColumn(name="user_id"), MockColumn(name="email"))
    tbl = MockTable(name="UserProfile", columns=cols)  # PascalCase table in snake_case profile
    ctx = _build_context((tbl,))
    rule = NamingConsistencyRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    assert "UserProfile" in res.findings[0].title
    assert res.findings[0].severity == DiagnosticSeverity.INFORMATIONAL


# ---------------------------------------------------------------------------
# DERA-MNT-004: Reserved Word Tests
# ---------------------------------------------------------------------------


def test_mnt_004_no_reserved_words_passes():
    cols = (MockColumn(name="account_id"), MockColumn(name="email_address"))
    tbl = MockTable(name="accounts", columns=cols)
    ctx = _build_context((tbl,))
    rule = ReservedWordUsageRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.PASS


def test_mnt_004_postgres_reserved_word_finding():
    cols = (MockColumn(name="id"), MockColumn(name="user"), MockColumn(name="select"))
    tbl = MockTable(name="order", columns=cols)  # 'order', 'user', 'select' are reserved
    ctx = _build_context((tbl,), dialect="postgresql")
    rule = ReservedWordUsageRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 3  # 1 table ('order') + 2 columns ('user', 'select')
    table_finding = next(f for f in res.findings if "Table" in f.title)
    col_findings = [f for f in res.findings if "Column" in f.title]

    assert table_finding.severity == DiagnosticSeverity.MEDIUM
    assert len(col_findings) == 2
    assert all(f.severity == DiagnosticSeverity.LOW for f in col_findings)


def test_mnt_004_mysql_specific_reserved_words():
    cols = (MockColumn(name="id"), MockColumn(name="separator"))
    tbl = MockTable(name="show", columns=cols)
    ctx = _build_context((tbl,), dialect="mysql")
    rule = ReservedWordUsageRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 2  # 1 table ('show') + 1 column ('separator')
    table_finding = next(f for f in res.findings if "Table" in f.title)
    col_finding = next(f for f in res.findings if "Column" in f.title)

    assert table_finding.severity == DiagnosticSeverity.MEDIUM
    assert col_finding.severity == DiagnosticSeverity.LOW


# ---------------------------------------------------------------------------
# DERA-MNT-005: Namespace Imbalance Tests
# ---------------------------------------------------------------------------


def test_mnt_005_single_namespace_not_applicable():
    ns = MockNamespace(name="public", tables=(MockTable(name="t1"), MockTable(name="t2")))
    ctx = _build_context((MockTable(name="t1"), MockTable(name="t2")), namespaces=(ns,))
    rule = NamespaceImbalanceRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.NOT_APPLICABLE


def test_mnt_005_imbalanced_namespaces_detection():
    # 19 tables in 'core', 1 table in 'audit' -> 95% concentration in core
    core_tables = tuple(MockTable(name=f"t_{i}") for i in range(19))
    audit_tables = (MockTable(name="log_event"),)
    ns_core = MockNamespace(name="core", tables=core_tables)
    ns_audit = MockNamespace(name="audit", tables=audit_tables)

    all_tables = core_tables + audit_tables
    ctx = _build_context(all_tables, namespaces=(ns_core, ns_audit))
    rule = NamespaceImbalanceRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    f = res.findings[0]
    assert f.rule_id == "DERA-MNT-005"
    assert f.severity == DiagnosticSeverity.INFORMATIONAL
    assert "Namespace Concentration" in f.title
    assert f.evidence[0].context_data["dominant_namespace"] == "core"


def test_mnt_005_empty_namespace_reported():
    # 15 tables in 'active', 0 in 'deprecated' -> imbalance detected and deprecated listed in empty_namespaces
    active_tables = tuple(MockTable(name=f"act_{i}") for i in range(15))
    ns1 = MockNamespace(name="active", tables=active_tables)
    ns2 = MockNamespace(name="deprecated", tables=())

    ctx = _build_context(active_tables, namespaces=(ns1, ns2))
    rule = NamespaceImbalanceRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    f = res.findings[0]
    assert "deprecated" in f.evidence[0].context_data["empty_namespaces"]


# ---------------------------------------------------------------------------
# DERA-MNT-006: Structural Coupling Tests
# ---------------------------------------------------------------------------


def _make_table_node(name: str) -> TableNode:
    prov = MetadataProvenance(source_engine="postgresql", native_identifier=name)
    return TableNode(
        object_id=f"node_{name}",
        native_name=name,
        namespace_name="public",
        column_count=5,
        primary_key_columns=("id",),
        completeness=MetadataCompleteness.COMPLETE,
        provenance=prov,
    )


def test_mnt_006_structural_coupling_finding():
    # Hub table referenced by 14 child tables -> total degree 14 (threshold 12)
    hub_node = _make_table_node("hub_table")
    child_nodes = [_make_table_node(f"child_{i}") for i in range(14)]
    all_nodes = [hub_node] + child_nodes

    edges = []
    prov = MetadataProvenance(source_engine="postgresql", native_identifier="fk")
    for i, child in enumerate(child_nodes):
        mapping = ColumnPairMapping(
            source_column_name="hub_id", referenced_column_name="id", ordinal_position=1
        )
        edges.append(
            ForeignKeyEdge(
                object_id=f"edge_{i}",
                native_name=f"fk_child_{i}_hub",
                source_table_id=child.object_id,
                referenced_table_id=hub_node.object_id,
                source_namespace=child.namespace_name,
                source_table_name=child.native_name,
                referenced_namespace=hub_node.namespace_name,
                referenced_table_name=hub_node.native_name,
                column_pairs=(mapping,),
                is_composite=False,
                is_self_referencing=False,
                is_cross_namespace=False,
                resolution_status=ResolutionStatus.RESOLVED,
                provenance=prov,
            )
        )

    cap = GraphCapabilityProfile(
        engine="postgresql", supports_foreign_keys=True, supports_composite_fks=True
    )
    graph = ForeignKeyGraph(
        contract_version="1.0.0",
        database_id="db_test",
        database_name="test_db",
        engine="postgresql",
        nodes=tuple(all_nodes),
        edges=tuple(edges),
        capability_profile=cap,
        provenance=MetadataProvenance(source_engine="postgresql"),
    )

    ctx = DiagnosticContext(graph=graph)
    rule = StructuralCouplingRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    f = res.findings[0]
    assert f.rule_id == "DERA-MNT-006"
    assert f.severity == DiagnosticSeverity.LOW
    assert "High Structural Coupling" in f.title
    assert f.evidence[0].context_data["total_degree"] == 14


# ---------------------------------------------------------------------------
# DERA-MNT-007: Complex Dependency Topology Tests
# ---------------------------------------------------------------------------


def test_mnt_007_complex_scc_finding():
    # 3-node cycle: A -> B -> C -> A
    node_a = _make_table_node("table_a")
    node_b = _make_table_node("table_b")
    node_c = _make_table_node("table_c")

    prov = MetadataProvenance(source_engine="postgresql", native_identifier="fk")
    mapping = ColumnPairMapping(
        source_column_name="ref_id", referenced_column_name="id", ordinal_position=1
    )

    e1 = ForeignKeyEdge(
        object_id="e1",
        native_name="fk_a_b",
        source_table_id=node_a.object_id,
        referenced_table_id=node_b.object_id,
        source_namespace=node_a.namespace_name,
        source_table_name=node_a.native_name,
        referenced_namespace=node_b.namespace_name,
        referenced_table_name=node_b.native_name,
        column_pairs=(mapping,),
        is_composite=False,
        is_self_referencing=False,
        is_cross_namespace=False,
        resolution_status=ResolutionStatus.RESOLVED,
        provenance=prov,
    )
    e2 = ForeignKeyEdge(
        object_id="e2",
        native_name="fk_b_c",
        source_table_id=node_b.object_id,
        referenced_table_id=node_c.object_id,
        source_namespace=node_b.namespace_name,
        source_table_name=node_b.native_name,
        referenced_namespace=node_c.namespace_name,
        referenced_table_name=node_c.native_name,
        column_pairs=(mapping,),
        is_composite=False,
        is_self_referencing=False,
        is_cross_namespace=False,
        resolution_status=ResolutionStatus.RESOLVED,
        provenance=prov,
    )
    e3 = ForeignKeyEdge(
        object_id="e3",
        native_name="fk_c_a",
        source_table_id=node_c.object_id,
        referenced_table_id=node_a.object_id,
        source_namespace=node_c.namespace_name,
        source_table_name=node_c.native_name,
        referenced_namespace=node_a.namespace_name,
        referenced_table_name=node_a.native_name,
        column_pairs=(mapping,),
        is_composite=False,
        is_self_referencing=False,
        is_cross_namespace=False,
        resolution_status=ResolutionStatus.RESOLVED,
        provenance=prov,
    )

    cap = GraphCapabilityProfile(
        engine="postgresql", supports_foreign_keys=True, supports_composite_fks=True
    )
    graph = ForeignKeyGraph(
        contract_version="1.0.0",
        database_id="db_test",
        database_name="test_db",
        engine="postgresql",
        nodes=(node_a, node_b, node_c),
        edges=(e1, e2, e3),
        capability_profile=cap,
        provenance=MetadataProvenance(source_engine="postgresql"),
    )

    ctx = DiagnosticContext(graph=graph)
    rule = ComplexDependencyTopologyRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    f = res.findings[0]
    assert f.rule_id == "DERA-MNT-007"
    assert f.severity == DiagnosticSeverity.LOW
    assert "Complex Dependency" in f.title
    assert f.evidence[0].context_data["member_count"] == 3


# ---------------------------------------------------------------------------
# DERA-MNT-008: LOB Column Concentration Tests
# ---------------------------------------------------------------------------


def test_mnt_008_lob_concentration_passes():
    cols = (
        MockColumn(name="id", native_data_type="int"),
        MockColumn(name="title", native_data_type="varchar(100)"),
        MockColumn(name="content", native_data_type="text"),
    )
    tbl = MockTable(name="posts", columns=cols)
    ctx = _build_context((tbl,))
    rule = LobConcentrationRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.PASS


def test_mnt_008_lob_concentration_finding():
    # 5 LOB columns triggers threshold 4 -> INFORMATIONAL severity
    cols = (
        MockColumn(name="id", native_data_type="int"),
        MockColumn(name="raw_body", native_data_type="text"),
        MockColumn(name="rendered_body", native_data_type="longtext"),
        MockColumn(name="document_blob", native_data_type="blob"),
        MockColumn(name="metadata_json", native_data_type="clob"),
        MockColumn(name="avatar", native_data_type="bytea"),
    )
    tbl = MockTable(name="unstructured_payloads", columns=cols)
    ctx = _build_context((tbl,))
    rule = LobConcentrationRule()
    res = rule.evaluate(ctx)

    assert res.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(res.findings) == 1
    f = res.findings[0]
    assert f.rule_id == "DERA-MNT-008"
    assert f.severity == DiagnosticSeverity.INFORMATIONAL
    assert "LOB Column Concentration" in f.title
    assert f.evidence[0].observed_value == 5
