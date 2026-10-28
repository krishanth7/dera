"""Tests for multi-severity integrity validation, strict mode, and diagnostic findings."""

from __future__ import annotations

import pytest
from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.dependencies.analyzer import DependencyAnalyzer
from dera.reverse_engineering.dependencies.errors import DependencyValidationError
from dera.reverse_engineering.dependencies.models import (
    DEPENDENCY_ANALYSIS_CONTRACT_VERSION,
    CycleReport,
    DependencyAnalysisResult,
    DependencyNodeMetrics,
    DependencyOrdering,
    TopologicalLevel,
)
from dera.reverse_engineering.dependencies.validation import (
    ValidationMode,
    validate_dependency_analysis,
)
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder

from tests.reverse_engineering.phase_6_4.fixtures import (
    analyze_database,
    make_ecommerce_schema,
    make_mutual_cycle_schema,
)


def test_validation_clean_dag():
    """Verify clean acyclic schema produces zero error validation findings."""
    db = make_ecommerce_schema()
    res = analyze_database(db)

    errors = [f for f in res.validation_findings if f.severity == "ERROR"]
    assert len(errors) == 0


def test_validation_unbreakable_cycle_warning_permissive():
    """Verify unbreakable cycle produces a WARNING in permissive mode."""
    db = make_mutual_cycle_schema(author_nullable=False, book_nullable=False)
    res = analyze_database(db)

    unbreakable_findings = [f for f in res.validation_findings if f.rule_id == "DEP_UNBREAKABLE_CYCLE"]
    assert len(unbreakable_findings) == 1
    assert unbreakable_findings[0].severity == "WARNING"


def test_validation_strict_mode_rejection():
    """Verify STRICT mode raises DependencyValidationError on unbreakable cycles."""
    db = make_mutual_cycle_schema(author_nullable=False, book_nullable=False)
    schema = SchemaBuilder.from_canonical_database(db)
    graph = ForeignKeyGraphBuilder.from_schema(schema)

    analyzer = DependencyAnalyzer()
    with pytest.raises(DependencyValidationError):
        analyzer.analyze(graph, schema=schema, mode=ValidationMode.STRICT)


def test_validation_ordering_completeness_check():
    """Verify validation detects missing nodes from creation order."""
    ordering = DependencyOrdering(
        is_pure_dag=True,
        creation_order=("tbl_a",),  # Missing tbl_b!
        drop_order=("tbl_a",),
        levels=(TopologicalLevel(level=0, node_ids=("tbl_a",)),),
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
    dummy_metric_a = DependencyNodeMetrics(
        node_id="tbl_a",
        in_degree=0,
        out_degree=0,
        transitive_dependency_count=0,
        transitive_dependent_count=0,
        depth_level=0,
        is_root=True,
        is_leaf=True,
        is_in_cycle=False,
    )
    dummy_metric_b = DependencyNodeMetrics(
        node_id="tbl_b",
        in_degree=0,
        out_degree=0,
        transitive_dependency_count=0,
        transitive_dependent_count=0,
        depth_level=0,
        is_root=True,
        is_leaf=True,
        is_in_cycle=False,
    )
    result = DependencyAnalysisResult(
        contract_version=DEPENDENCY_ANALYSIS_CONTRACT_VERSION,
        database_id="db-1",
        source_graph_hash="x" * 64,
        node_count=2,
        edge_count=0,
        is_dag=True,
        ordering=ordering,
        cycle_report=cycle_report,
        node_metrics={
            "tbl_a": dummy_metric_a,
            "tbl_b": dummy_metric_b,
        },
    )

    findings = validate_dependency_analysis(result, mode=ValidationMode.PERMISSIVE)
    missing = [f for f in findings if f.rule_id == "DEP_ORDERING_COMPLETENESS"]
    assert len(missing) == 1
    assert missing[0].severity == "ERROR"
