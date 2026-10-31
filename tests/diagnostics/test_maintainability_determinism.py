"""DERA Phase 8.4 — Determinism and Permutation Invariance Tests.

Verifies that all Phase 8.4 schema maintainability diagnostic rules produce
bitwise-identical, strictly deterministic findings, ordering, and fingerprints
under input table, column, namespace, and graph edge reorderings.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from dera.diagnostics.context import DiagnosticContext, DiagnosticEngineConfig
from dera.diagnostics.rules.maintainability import ALL_PHASE_8_4_RULES
from dera.metadata.enums import MetadataCompleteness
from dera.metadata.provenance import MetadataProvenance
from dera.reverse_engineering.graph.capabilities import GraphCapabilityProfile
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.graph.nodes import TableNode
from dera.reverse_engineering.references import ResolutionStatus


@dataclass
class MockColumn:
    name: str
    id: str
    is_nullable: bool = True
    default_expression: str | None = None
    is_identity: bool = False
    is_generated: bool = False
    native_data_type: str = "varchar(255)"
    canonical_type: str = "VARCHAR"


@dataclass
class MockTable:
    name: str
    id: str
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


def _make_table_node(name: str, namespace: str = "public") -> TableNode:
    prov = MetadataProvenance(source_engine="postgresql", native_identifier=name)
    return TableNode(
        object_id=f"node_{namespace}_{name}",
        native_name=name,
        namespace_name=namespace,
        column_count=5,
        primary_key_columns=("id",),
        completeness=MetadataCompleteness.COMPLETE,
        provenance=prov,
    )


def test_maintainability_permutation_invariance():
    # Construct a rich test schema with multiple namespaces, wide tables,
    # reserved words, nullability, and cyclic graph dependencies
    cols_wide = tuple(
        MockColumn(name=f"col_{i}", id=f"c_w_{i}", is_nullable=(i % 2 == 0)) for i in range(55)
    )
    tbl_wide = MockTable(name="wide_table", id="t_wide", columns=cols_wide, schema_name="core")

    cols_mixed = (
        MockColumn(name="order_id", id="c_m_1", is_nullable=False, native_data_type="bigint"),
        MockColumn(
            name="user", id="c_m_2", is_nullable=True, native_data_type="varchar(100)"
        ),  # reserved
        MockColumn(
            name="select", id="c_m_3", is_nullable=True, native_data_type="varchar(100)"
        ),  # reserved
        MockColumn(
            name="CustomerName", id="c_m_4", is_nullable=True, native_data_type="text"
        ),  # PascalCase & LOB
        MockColumn(
            name="itemPayload", id="c_m_5", is_nullable=True, native_data_type="blob"
        ),  # camelCase & LOB
        MockColumn(
            name="auditRaw", id="c_m_6", is_nullable=True, native_data_type="longtext"
        ),  # LOB
        MockColumn(
            name="archiveZip", id="c_m_7", is_nullable=True, native_data_type="bytea"
        ),  # LOB
    )
    tbl_orders = MockTable(
        name="order", id="t_order", columns=cols_mixed, schema_name="core"
    )  # reserved name

    core_tables = [tbl_wide, tbl_orders] + [
        MockTable(name=f"core_tab_{i}", id=f"t_core_{i}", schema_name="core") for i in range(15)
    ]
    audit_tables = [
        MockTable(name="audit_log", id="t_audit_1", schema_name="audit"),
    ]

    ns_core = MockNamespace(name="core", tables=tuple(core_tables))
    ns_audit = MockNamespace(name="audit", tables=tuple(audit_tables))
    ns_empty = MockNamespace(name="deprecated", tables=())
    all_namespaces = [ns_core, ns_audit, ns_empty]

    # Graph with 3-node cycle
    node_a = _make_table_node("table_a", "core")
    node_b = _make_table_node("table_b", "core")
    node_c = _make_table_node("table_c", "core")
    node_hub = _make_table_node("hub_table", "core")
    child_nodes = [_make_table_node(f"ch_{i}", "core") for i in range(14)]

    all_graph_nodes = [node_a, node_b, node_c, node_hub] + child_nodes

    prov = MetadataProvenance(source_engine="postgresql", native_identifier="fk")
    mapping = ColumnPairMapping(
        source_column_name="ref_id", referenced_column_name="id", ordinal_position=1
    )

    edges = [
        ForeignKeyEdge(
            object_id="e1",
            native_name="fk_a_b",
            source_table_id=node_a.object_id,
            referenced_table_id=node_b.object_id,
            source_namespace="core",
            source_table_name="table_a",
            referenced_namespace="core",
            referenced_table_name="table_b",
            column_pairs=(mapping,),
            is_composite=False,
            is_self_referencing=False,
            is_cross_namespace=False,
            resolution_status=ResolutionStatus.RESOLVED,
            provenance=prov,
        ),
        ForeignKeyEdge(
            object_id="e2",
            native_name="fk_b_c",
            source_table_id=node_b.object_id,
            referenced_table_id=node_c.object_id,
            source_namespace="core",
            source_table_name="table_b",
            referenced_namespace="core",
            referenced_table_name="table_c",
            column_pairs=(mapping,),
            is_composite=False,
            is_self_referencing=False,
            is_cross_namespace=False,
            resolution_status=ResolutionStatus.RESOLVED,
            provenance=prov,
        ),
        ForeignKeyEdge(
            object_id="e3",
            native_name="fk_c_a",
            source_table_id=node_c.object_id,
            referenced_table_id=node_a.object_id,
            source_namespace="core",
            source_table_name="table_c",
            referenced_namespace="core",
            referenced_table_name="table_a",
            column_pairs=(mapping,),
            is_composite=False,
            is_self_referencing=False,
            is_cross_namespace=False,
            resolution_status=ResolutionStatus.RESOLVED,
            provenance=prov,
        ),
    ]

    for i, ch in enumerate(child_nodes):
        edges.append(
            ForeignKeyEdge(
                object_id=f"e_hub_{i}",
                native_name=f"fk_ch_{i}_hub",
                source_table_id=ch.object_id,
                referenced_table_id=node_hub.object_id,
                source_namespace="core",
                source_table_name=ch.native_name,
                referenced_namespace="core",
                referenced_table_name=node_hub.native_name,
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

    def _build_test_context(ns_list, g_nodes, g_edges) -> DiagnosticContext:
        db = MockDatabase(name="test_db", namespaces=tuple(ns_list))
        schema = MockSchemaRepresentation(database=db)
        graph = ForeignKeyGraph(
            contract_version="1.0.0",
            database_id="db_test",
            database_name="test_db",
            engine="postgresql",
            nodes=tuple(g_nodes),
            edges=tuple(g_edges),
            capability_profile=cap,
            provenance=MetadataProvenance(source_engine="postgresql"),
        )
        return DiagnosticContext(
            schema=schema,
            graph=graph,
            source_engine="postgresql",
            config=DiagnosticEngineConfig(),
        )

    # 1. Baseline Evaluation
    base_ctx = _build_test_context(all_namespaces, all_graph_nodes, edges)
    baseline_results = {}
    for rule in ALL_PHASE_8_4_RULES:
        eval_res = rule.evaluate(base_ctx)
        baseline_results[rule.metadata.rule_id] = [
            (f.object_id, f.title, f.fingerprint, f.severity.value) for f in eval_res.findings
        ]

    # Verify that maintainability findings were actually detected in baseline
    total_findings = sum(len(f_list) for f_list in baseline_results.values())
    assert total_findings > 0, "Baseline must detect findings across Phase 8.4 rules"

    # 2. Run 5 Permutations with Seeded RNG
    rng = random.Random(1337)
    for p in range(5):
        shuffled_ns = list(all_namespaces)
        rng.shuffle(shuffled_ns)

        # Shuffle tables within namespaces
        new_ns_list = []
        for ns in shuffled_ns:
            shuffled_tables = list(ns.tables)
            rng.shuffle(shuffled_tables)
            new_ns_list.append(MockNamespace(name=ns.name, tables=tuple(shuffled_tables)))

        shuffled_nodes = list(all_graph_nodes)
        rng.shuffle(shuffled_nodes)

        shuffled_edges = list(edges)
        rng.shuffle(shuffled_edges)

        perm_ctx = _build_test_context(new_ns_list, shuffled_nodes, shuffled_edges)

        for rule in ALL_PHASE_8_4_RULES:
            perm_eval = rule.evaluate(perm_ctx)
            perm_findings = [
                (f.object_id, f.title, f.fingerprint, f.severity.value) for f in perm_eval.findings
            ]

            assert perm_findings == baseline_results[rule.metadata.rule_id], (
                f"Determinism violation under permutation {p} for rule {rule.metadata.rule_id}!\n"
                f"Expected: {baseline_results[rule.metadata.rule_id]}\n"
                f"Got:      {perm_findings}"
            )
