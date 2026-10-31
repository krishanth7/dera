"""Unit tests for Phase 8.4 Maintainability Metrics.

Covers schema complexity, table metrics, naming compliance, namespace metrics,
and structural coupling metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dera.diagnostics.metrics.coupling_metrics import compute_all_coupling_metrics
from dera.diagnostics.metrics.models import (
    NamingComplianceMetrics,
    SchemaComplexityMetrics,
    TableMaintainabilityMetrics,
)
from dera.diagnostics.metrics.namespace_metrics import (
    compute_namespace_imbalance_ratio,
    compute_namespace_metrics,
)
from dera.diagnostics.metrics.naming_metrics import (
    NamingProfile,
    compute_naming_compliance,
    is_reserved_word,
    matches_naming_profile,
)
from dera.diagnostics.metrics.schema_metrics import compute_schema_complexity
from dera.diagnostics.metrics.table_metrics import (
    compute_all_table_metrics,
    compute_table_metrics,
    is_lob_column,
)
from dera.metadata.enums import MetadataCompleteness
from dera.metadata.provenance import MetadataProvenance
from dera.reverse_engineering.dependencies.analyzer import DependencyAnalyzer
from dera.reverse_engineering.graph.capabilities import GraphCapabilityProfile
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.graph.nodes import TableNode
from dera.reverse_engineering.references import ResolutionStatus


# Lightweight test mocks
@dataclass
class MockColumn:
    name: str
    is_nullable: bool = True
    default_expression: str | None = None
    is_identity: bool = False
    is_generated: bool = False
    native_data_type: str = "varchar(255)"
    canonical_type: str = "VARCHAR"


@dataclass
class MockIndex:
    name: str


@dataclass
class MockConstraint:
    name: str


@dataclass
class MockFK:
    name: str


@dataclass
class MockTable:
    name: str
    id: str = "tbl_id"
    columns: tuple[MockColumn, ...] = ()
    indexes: tuple[MockIndex, ...] = ()
    foreign_keys: tuple[MockFK, ...] = ()
    unique_constraints: tuple = ()
    check_constraints: tuple = ()
    primary_key: Any = None
    schema_name: str | None = "public"


@dataclass
class MockNamespace:
    name: str
    tables: tuple[MockTable, ...] = ()
    views: tuple = ()


# -----------------------------------------------------------------------------
# Table Metrics & LOB Column Tests
# -----------------------------------------------------------------------------


def test_is_lob_column():
    assert is_lob_column(MockColumn(name="c1", native_data_type="text")) is True
    assert is_lob_column(MockColumn(name="c2", native_data_type="LONGTEXT")) is True
    assert is_lob_column(MockColumn(name="c3", native_data_type="blob")) is True
    assert is_lob_column(MockColumn(name="c4", native_data_type="bytea")) is True
    assert is_lob_column(MockColumn(name="c5", native_data_type="clob")) is True
    assert is_lob_column(MockColumn(name="c6", native_data_type="varbinary(max)")) is True
    assert is_lob_column(MockColumn(name="c7", native_data_type="varchar(255)")) is False
    assert is_lob_column(MockColumn(name="c8", native_data_type="integer")) is False
    assert is_lob_column(MockColumn(name="c9", native_data_type="boolean")) is False


def test_compute_table_metrics():
    cols = (
        MockColumn(name="id", is_nullable=False, is_identity=True, native_data_type="bigint"),
        MockColumn(
            name="title",
            is_nullable=False,
            default_expression="'untitled'",
            native_data_type="varchar(100)",
        ),
        MockColumn(name="description", is_nullable=True, native_data_type="text"),
        MockColumn(name="metadata", is_nullable=True, native_data_type="jsonb"),
        MockColumn(name="raw_content", is_nullable=True, native_data_type="bytea"),
    )
    table = MockTable(name="articles", id="t_articles", columns=cols)
    metrics = compute_table_metrics(table)

    assert isinstance(metrics, TableMaintainabilityMetrics)
    assert metrics.table_name == "articles"
    assert metrics.object_id == "t_articles"
    assert metrics.column_count == 5
    assert metrics.nullable_column_count == 3
    assert metrics.nullability_ratio == 0.6
    assert metrics.default_expression_count == 1
    assert metrics.identity_column_count == 1
    assert metrics.generated_column_count == 0
    assert metrics.lob_column_count == 2  # text, bytea


def test_compute_table_metrics_empty():
    table = MockTable(name="empty_table", columns=())
    metrics = compute_table_metrics(table)
    assert metrics.column_count == 0
    assert metrics.nullability_ratio == 0.0
    assert metrics.lob_column_count == 0


def test_compute_all_table_metrics():
    t1 = MockTable(name="b_table", schema_name="public")
    t2 = MockTable(name="a_table", schema_name="public")
    all_metrics = compute_all_table_metrics([t1, t2])
    assert len(all_metrics) == 2
    assert all_metrics[0].table_name == "a_table"
    assert all_metrics[1].table_name == "b_table"


# -----------------------------------------------------------------------------
# Schema Complexity Tests
# -----------------------------------------------------------------------------


def test_compute_schema_complexity():
    t1 = MockTable(
        name="users",
        columns=(MockColumn(name="id"), MockColumn(name="email")),
        indexes=(MockIndex(name="ix_users_email"),),
        primary_key="pk_users",
        foreign_keys=(),
    )
    t2 = MockTable(
        name="orders",
        columns=(MockColumn(name="id"), MockColumn(name="user_id"), MockColumn(name="total")),
        indexes=(),
        primary_key="pk_orders",
        foreign_keys=(MockFK(name="fk_orders_users"),),
    )
    ns1 = MockNamespace(name="public", tables=(t1, t2))

    metrics = compute_schema_complexity(tables=(t1, t2), namespaces=(ns1,))
    assert isinstance(metrics, SchemaComplexityMetrics)
    assert metrics.table_count == 2
    assert metrics.column_count == 5
    assert metrics.index_count == 1
    assert metrics.constraint_count == 3  # 2 PKs + 1 FK
    assert metrics.foreign_key_count == 1
    assert metrics.namespace_count == 1
    assert metrics.avg_columns_per_table == 2.5
    assert metrics.avg_constraints_per_table == 1.5


# -----------------------------------------------------------------------------
# Naming Profile & Compliance Tests
# -----------------------------------------------------------------------------


def test_matches_naming_profile():
    # snake_case
    assert matches_naming_profile("order_items", NamingProfile.SNAKE_CASE) is True
    assert matches_naming_profile("orderitems", NamingProfile.SNAKE_CASE) is True
    assert matches_naming_profile("orderItems", NamingProfile.SNAKE_CASE) is False
    assert matches_naming_profile("OrderItems", NamingProfile.SNAKE_CASE) is False
    assert matches_naming_profile("order-items", NamingProfile.SNAKE_CASE) is False

    # camelCase
    assert matches_naming_profile("orderItems", NamingProfile.CAMEL_CASE) is True
    assert matches_naming_profile("id", NamingProfile.CAMEL_CASE) is True
    assert matches_naming_profile("order_items", NamingProfile.CAMEL_CASE) is False
    assert matches_naming_profile("OrderItems", NamingProfile.CAMEL_CASE) is False

    # PascalCase
    assert matches_naming_profile("OrderItems", NamingProfile.PASCAL_CASE) is True
    assert matches_naming_profile("Order", NamingProfile.PASCAL_CASE) is True
    assert matches_naming_profile("orderItems", NamingProfile.PASCAL_CASE) is False
    assert matches_naming_profile("order_items", NamingProfile.PASCAL_CASE) is False

    # kebab-case
    assert matches_naming_profile("order-items", NamingProfile.KEBAB_CASE) is True
    assert matches_naming_profile("order_items", NamingProfile.KEBAB_CASE) is False

    # UPPER_SNAKE_CASE
    assert matches_naming_profile("ORDER_ITEMS", NamingProfile.UPPER_SNAKE_CASE) is True
    assert matches_naming_profile("order_items", NamingProfile.UPPER_SNAKE_CASE) is False


def test_is_reserved_word():
    # PostgreSQL
    assert is_reserved_word("select", "postgresql") is True
    assert is_reserved_word("user", "postgresql") is True
    assert is_reserved_word("analyse", "postgresql") is True
    assert is_reserved_word("order_items", "postgresql") is False

    # MySQL
    assert is_reserved_word("xor", "mysql") is True
    assert is_reserved_word("separator", "mysql") is True
    assert is_reserved_word("show", "mysql") is True
    assert is_reserved_word("analyse", "mysql") is False

    # SQLite
    assert is_reserved_word("autoincrement", "sqlite") is True
    assert is_reserved_word("pragma", "sqlite") is True
    assert is_reserved_word("glob", "sqlite") is True

    # Case insensitive
    assert is_reserved_word("SELECT", "postgresql") is True
    assert is_reserved_word("Table", "mysql") is True


def test_compute_naming_compliance():
    identifiers = ["order_id", "customer_id", "total_amount", "createdDate", "UpdatedDate"]
    compliance = compute_naming_compliance(
        identifiers=identifiers,
        profile_name=NamingProfile.SNAKE_CASE,
    )
    assert isinstance(compliance, NamingComplianceMetrics)
    assert compliance.total_evaluated == 5
    assert compliance.compliant_count == 3
    assert compliance.non_compliant_count == 2
    assert compliance.compliance_ratio == 0.6


# -----------------------------------------------------------------------------
# Namespace Metrics Tests
# -----------------------------------------------------------------------------


def test_compute_namespace_metrics():
    t_auth1 = MockTable(name="users")
    t_auth2 = MockTable(name="sessions")
    t_bill = MockTable(name="invoices")

    ns1 = MockNamespace(name="auth", tables=(t_auth1, t_auth2))
    ns2 = MockNamespace(name="billing", tables=(t_bill,))
    ns3 = MockNamespace(name="empty_ns", tables=())

    metrics = compute_namespace_metrics((ns1, ns2, ns3))
    assert len(metrics) == 3
    m_dict = {m.namespace_name: m for m in metrics}

    assert m_dict["auth"].table_count == 2
    assert m_dict["auth"].object_share_ratio == round(2 / 3, 4)
    assert m_dict["billing"].table_count == 1
    assert m_dict["empty_ns"].table_count == 0

    imbalance = compute_namespace_imbalance_ratio(metrics)
    assert imbalance == round(2 / 3, 4)


def test_compute_namespace_imbalance_ratio_single():
    ns = MockNamespace(name="public", tables=(MockTable(name="t1"), MockTable(name="t2")))
    metrics = compute_namespace_metrics((ns,))
    assert compute_namespace_imbalance_ratio(metrics) == 0.0


# -----------------------------------------------------------------------------
# Coupling Metrics Tests
# -----------------------------------------------------------------------------


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


def test_coupling_metrics():
    node_a = _make_table_node("table_a")
    node_b = _make_table_node("table_b")
    node_c = _make_table_node("table_c")

    prov = MetadataProvenance(source_engine="postgresql", native_identifier="fk")
    mapping_ab = ColumnPairMapping(
        source_column_name="b_id",
        referenced_column_name="id",
        ordinal_position=1,
    )
    edge1 = ForeignKeyEdge(
        object_id="edge_1",
        native_name="fk_a_b",
        source_table_id=node_a.object_id,
        referenced_table_id=node_b.object_id,
        source_namespace=node_a.namespace_name,
        source_table_name=node_a.native_name,
        referenced_namespace=node_b.namespace_name,
        referenced_table_name=node_b.native_name,
        column_pairs=(mapping_ab,),
        is_composite=False,
        is_self_referencing=False,
        is_cross_namespace=False,
        resolution_status=ResolutionStatus.RESOLVED,
        provenance=prov,
    )

    mapping_bc = ColumnPairMapping(
        source_column_name="c_id",
        referenced_column_name="id",
        ordinal_position=1,
    )
    edge2 = ForeignKeyEdge(
        object_id="edge_2",
        native_name="fk_b_c",
        source_table_id=node_b.object_id,
        referenced_table_id=node_c.object_id,
        source_namespace=node_b.namespace_name,
        source_table_name=node_b.native_name,
        referenced_namespace=node_c.namespace_name,
        referenced_table_name=node_c.native_name,
        column_pairs=(mapping_bc,),
        is_composite=False,
        is_self_referencing=False,
        is_cross_namespace=False,
        resolution_status=ResolutionStatus.RESOLVED,
        provenance=prov,
    )

    cap = GraphCapabilityProfile(
        engine="postgresql",
        supports_foreign_keys=True,
        supports_composite_fks=True,
    )
    graph = ForeignKeyGraph(
        contract_version="1.0.0",
        database_id="db_test",
        database_name="test_db",
        engine="postgresql",
        nodes=(node_a, node_b, node_c),
        edges=(edge1, edge2),
        capability_profile=cap,
        provenance=MetadataProvenance(source_engine="postgresql"),
    )

    analyzer = DependencyAnalyzer()
    deps = analyzer.analyze(graph)
    all_metrics = compute_all_coupling_metrics(graph, deps)

    metrics_by_node = {m.node_id: m for m in all_metrics}
    assert node_a.object_id in metrics_by_node
    assert node_b.object_id in metrics_by_node
    assert node_c.object_id in metrics_by_node

    m_a = metrics_by_node[node_a.object_id]
    m_b = metrics_by_node[node_b.object_id]
    m_c = metrics_by_node[node_c.object_id]

    # In DependencyAnalyzer:
    # edge1 is node_a -> node_b (node_a depends on node_b)
    assert m_a.total_degree >= 1
    assert m_b.total_degree >= 1
    assert m_c.total_degree >= 1
