"""Tests for Phase 6.4 Dependency Analysis domain models and contracts."""

from __future__ import annotations

import pytest
from dera.reverse_engineering.dependencies.models import (
    DEPENDENCY_ANALYSIS_CONTRACT_VERSION,
    BreakabilityStrategy,
    CycleInstance,
    CycleKind,
    CycleReport,
    DependencyAnalysisResult,
    DependencyEdge,
    DependencyKind,
    DependencyNodeMetrics,
    DependencyOrdering,
    TopologicalLevel,
)
from pydantic import ValidationError


def test_dependency_models_immutability():
    """Verify that all core dependency models are strictly frozen."""
    edge = DependencyEdge(
        edge_id="edge-1",
        dependent_id="tbl-orders",
        referenced_id="tbl-customers",
        kind=DependencyKind.TABLE_FOREIGN_KEY,
        is_nullable=True,
    )
    with pytest.raises(ValidationError):
        edge.is_nullable = False  # type: ignore

    level = TopologicalLevel(level=0, node_ids=("tbl-1", "tbl-2"))
    with pytest.raises(ValidationError):
        level.level = 1  # type: ignore

    metrics = DependencyNodeMetrics(
        node_id="tbl-1",
        in_degree=0,
        out_degree=2,
        transitive_dependency_count=0,
        transitive_dependent_count=3,
        depth_level=0,
        is_root=True,
        is_leaf=False,
        is_in_cycle=False,
    )
    with pytest.raises(ValidationError):
        metrics.is_root = False  # type: ignore


def test_dependency_models_forbid_extra_fields():
    """Verify extra attributes are forbidden across dependency models."""
    with pytest.raises(ValidationError):
        DependencyEdge(  # type: ignore
            edge_id="e1",
            dependent_id="t1",
            referenced_id="t2",
            unexpected_attribute="injected",
        )

    with pytest.raises(ValidationError):
        CycleInstance(  # type: ignore
            cycle_id="c1",
            kind=CycleKind.MUTUAL,
            node_ids=("t1", "t2"),
            hacked="exploit",
        )


def test_cycle_report_attributes():
    """Verify CycleReport statistics and aggregation integrity."""
    c1 = CycleInstance(
        cycle_id="c-self",
        kind=CycleKind.SELF_REFERENCING,
        node_ids=("t_emp",),
        is_breakable=True,
        recommended_break_strategy=BreakabilityStrategy.NULLABLE_FOREIGN_KEY,
    )
    report = CycleReport(
        has_cycles=True,
        cycle_count=1,
        scc_count=1,
        cyclic_scc_count=1,
        self_referencing_count=1,
        mutual_count=0,
        indirect_count=0,
        complex_count=0,
        breakable_cycle_count=1,
        unbreakable_cycle_count=0,
        cycles=(c1,),
        sccs=(),
    )
    assert report.has_cycles is True
    assert report.self_referencing_count == 1
    assert report.breakable_cycle_count == 1
    assert report.unbreakable_cycle_count == 0


def test_dependency_analysis_result_hash_deterministic():
    """Verify that compute_hash() produces a stable 64-char hex string."""
    ordering = DependencyOrdering(
        is_pure_dag=True,
        creation_order=("t1", "t2"),
        drop_order=("t2", "t1"),
        levels=(
            TopologicalLevel(level=0, node_ids=("t1",)),
            TopologicalLevel(level=1, node_ids=("t2",)),
        ),
    )
    cycle_report = CycleReport(
        has_cycles=False,
        cycle_count=0,
        scc_count=2,
        cyclic_scc_count=0,
        self_referencing_count=0,
        mutual_count=0,
        indirect_count=0,
        complex_count=0,
        breakable_cycle_count=0,
        unbreakable_cycle_count=0,
        cycles=(),
        sccs=(),
    )
    res = DependencyAnalysisResult(
        contract_version=DEPENDENCY_ANALYSIS_CONTRACT_VERSION,
        workspace_id="ws-1",
        database_id="db-1",
        source_graph_hash="a" * 64,
        node_count=2,
        edge_count=1,
        is_dag=True,
        ordering=ordering,
        cycle_report=cycle_report,
    )
    h1 = res.compute_hash()
    h2 = res.compute_hash()
    assert len(h1) == 64
    assert h1 == h2
    assert res.get_creation_order() == ("t1", "t2")
    assert res.get_drop_order() == ("t2", "t1")
