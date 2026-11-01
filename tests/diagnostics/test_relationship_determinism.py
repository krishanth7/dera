"""DERA Phase 8.3 — Determinism and Invariance Tests.

Verifies that all Phase 8.3 relationship and dependency diagnostic rules
produce strictly bitwise-identical, deterministic findings and fingerprints
under input graph node, edge, and reference reorderings.
"""

from __future__ import annotations

import random

from dera.diagnostics.context import DiagnosticContext
from dera.diagnostics.rules.relationships import ALL_PHASE_8_3_RULES
from dera.metadata.enums import MetadataCompleteness
from dera.metadata.provenance import MetadataProvenance
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge, ResolutionStatus
from dera.reverse_engineering.graph.models import (
    ForeignKeyGraph,
    UnresolvedReason,
    UnresolvedReference,
)
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


def test_phase_8_3_rules_determinism_under_permutations():
    # Build a complex graph containing:
    # 1. Multi-node cycle
    # 2. Self-loop
    # 3. Cross-namespace edge
    # 4. Composite mismatch
    # 5. Missing endpoint edge
    # 6. Unresolved reference
    t1 = _make_table_node("org", "auth")
    t2 = _make_table_node("user", "public")
    t3 = _make_table_node("account", "public")
    t4 = _make_table_node("txn", "public")

    e1 = _make_fk_edge(t2, t1, "fk_user_org", is_cross_namespace=True)  # cross-namespace
    e2 = _make_fk_edge(t2, t3, "fk_user_account")  # cycle part 1
    e3 = _make_fk_edge(t3, t2, "fk_account_user")  # cycle part 2
    e4 = _make_fk_edge(t1, t1, "fk_org_parent", is_self=True)  # self-loop
    e5 = _make_fk_edge(
        t4, t3, "fk_txn_account", (("acc_id", "id"), ("extra_col", ""))
    )  # composite mismatch

    # Edge pointing to non-existent node
    ghost_edge = ForeignKeyEdge(
        object_id="edge_ghost",
        native_name="fk_ghost",
        source_table_id=t4.object_id,
        referenced_table_id="node_missing_ghost",
        source_namespace=t4.namespace_name,
        source_table_name=t4.native_name,
        referenced_namespace="public",
        referenced_table_name="ghost_table",
        column_pairs=(
            ColumnPairMapping(
                source_column_name="ghost_id",
                referenced_column_name="id",
                ordinal_position=1,
            ),
        ),
        is_composite=False,
        is_self_referencing=False,
        is_cross_namespace=False,
        resolution_status=ResolutionStatus.MISSING,
        provenance=MetadataProvenance(source_engine="postgresql", native_identifier="fk_ghost"),
    )

    unres = UnresolvedReference(
        foreign_key_id="fk_unres",
        native_name="fk_unres",
        source_table_id=t3.object_id,
        source_table_name="account",
        source_namespace="public",
        referenced_table_name="legacy_db",
        referenced_namespace="archive",
        declared_source_columns=("legacy_id",),
        declared_referenced_columns=("id",),
        reason=UnresolvedReason.REFERENCED_TABLE_NOT_FOUND,
        details="Table 'archive.legacy_db' not found.",
        provenance=MetadataProvenance(source_engine="postgresql", native_identifier="fk_unres"),
    )

    nodes = [t1, t2, t3, t4]
    edges = [e1, e2, e3, e4, e5, ghost_edge]
    unresolved = [unres]

    def _make_graph(n, e, u):
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
            nodes=tuple(n),
            edges=tuple(e),
            unresolved_references=tuple(u),
            capability_profile=cap,
            provenance=prov,
        )

    # Baseline run
    base_graph = _make_graph(nodes, edges, unresolved)
    base_ctx = DiagnosticContext(graph=base_graph)

    baseline_results = {}
    for rule in ALL_PHASE_8_3_RULES:
        eval_res = rule.evaluate(base_ctx)
        baseline_results[rule.metadata.rule_id] = [
            (f.object_id, f.title, f.fingerprint, f.severity.value) for f in eval_res.findings
        ]

    # Run 5 permutations with seeded RNG
    rng = random.Random(42)
    for trial in range(5):
        perm_nodes = list(nodes)
        rng.shuffle(perm_nodes)
        perm_edges = list(edges)
        rng.shuffle(perm_edges)
        perm_unres = list(unresolved)
        rng.shuffle(perm_unres)

        perm_graph = _make_graph(perm_nodes, perm_edges, perm_unres)
        perm_ctx = DiagnosticContext(graph=perm_graph)

        for rule in ALL_PHASE_8_3_RULES:
            eval_res = rule.evaluate(perm_ctx)
            findings_summary = [
                (f.object_id, f.title, f.fingerprint, f.severity.value) for f in eval_res.findings
            ]
            expected = baseline_results[rule.metadata.rule_id]
            assert findings_summary == expected, (
                f"Rule {rule.metadata.rule_id} produced non-deterministic findings on trial {trial}: "
                f"{findings_summary} != {expected}"
            )
