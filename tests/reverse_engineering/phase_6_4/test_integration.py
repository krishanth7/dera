"""End-to-end integration tests: Canonical -> Schema -> Reconstruction -> Graph -> Dependency Analysis."""

from __future__ import annotations

from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.dependencies.analyzer import DependencyAnalyzer
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.reconstruction.builder import StructuralReconstructionBuilder

from tests.reverse_engineering.phase_6_4.fixtures import (
    make_ecommerce_schema,
    make_mutual_cycle_schema,
)


def test_full_reverse_engineering_pipeline():
    """Verify full 5-stage DERA reverse engineering engine pipeline."""
    # Step 1: Canonical Metadata
    canonical_db = make_ecommerce_schema()

    # Step 2: Phase 6.1 SchemaRepresentation
    schema = SchemaBuilder.from_canonical_database(canonical_db)
    assert schema is not None
    assert len(schema.namespaces[0].tables) == 7

    # Step 3: Phase 6.2 StructuralReconstruction
    recon = StructuralReconstructionBuilder().build_from_schema(schema)
    assert recon is not None
    assert len(recon.tables) == 7

    # Step 4: Phase 6.3 Foreign Key Relationship Graph
    graph = ForeignKeyGraphBuilder.from_reconstruction(recon)
    assert graph.node_count == 7
    assert graph.edge_count == 6

    # Step 5: Phase 6.4 Dependency Analysis & Cycle Detection
    analyzer = DependencyAnalyzer()
    dep_res = analyzer.analyze(graph, schema=schema)

    assert dep_res.is_dag is True
    assert dep_res.node_count == 7
    assert dep_res.edge_count == 6
    assert len(dep_res.ordering.creation_order) == 7
    assert len(dep_res.ordering.drop_order) == 7
    assert len(dep_res.ordering.levels) == 3
    assert dep_res.cycle_report.has_cycles is False
    assert len(dep_res.root_node_ids) == 3
    assert len(dep_res.leaf_node_ids) == 3
    assert len(dep_res.isolated_node_ids) == 1


def test_full_pipeline_cyclic_handling():
    """Verify full pipeline properly processes and classifies cyclic schemas."""
    canonical_db = make_mutual_cycle_schema()
    schema = SchemaBuilder.from_canonical_database(canonical_db)
    recon = StructuralReconstructionBuilder().build_from_schema(schema)
    graph = ForeignKeyGraphBuilder.from_reconstruction(recon)

    dep_res = DependencyAnalyzer().analyze(graph, schema=schema)
    assert dep_res.is_dag is False
    assert dep_res.cycle_report.cycle_count == 1
    assert dep_res.cycle_report.mutual_count == 1
