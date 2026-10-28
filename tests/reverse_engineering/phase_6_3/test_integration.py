"""Integration tests executing the full pipeline: Canonical -> Reconstruction -> Relationship Graph."""

from __future__ import annotations

from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.reconstruction.builder import StructuralReconstructionBuilder

from tests.reverse_engineering.phase_6_3.fixtures import (
    make_composite_fk_schema,
    make_parallel_edges_schema,
    make_self_referencing_schema,
    make_simple_fk_schema,
)


def test_full_pipeline_simple_fk():
    """Verify end-to-end integration: Canonical -> SchemaRepresentation -> Reconstruction -> Graph."""
    canonical_db = make_simple_fk_schema()

    # Step 1: Phase 6.1 SchemaRepresentation
    schema = SchemaBuilder.from_canonical_database(canonical_db)
    assert schema is not None

    # Step 2: Phase 6.2 StructuralReconstruction
    recon = StructuralReconstructionBuilder().build_from_schema(schema)
    assert recon is not None
    assert len(recon.tables) == 2

    # Step 3: Phase 6.3 Foreign Key Relationship Graph
    graph_from_recon = ForeignKeyGraphBuilder.from_reconstruction(recon)
    assert graph_from_recon.node_count == 2
    assert graph_from_recon.edge_count == 1

    graph_from_schema = ForeignKeyGraphBuilder.from_schema(schema)
    assert graph_from_schema.node_count == 2
    assert graph_from_schema.edge_count == 1

    # Verify structural query parity
    cust = graph_from_recon.get_node_by_name("customers")
    orders = graph_from_recon.get_node_by_name("orders")
    assert cust is not None and orders is not None
    assert len(graph_from_recon.relationships_between(orders.object_id, cust.object_id)) == 1


def test_full_pipeline_composite_keys():
    canonical_db = make_composite_fk_schema()
    schema = SchemaBuilder.from_canonical_database(canonical_db)
    recon = StructuralReconstructionBuilder().build_from_schema(schema)
    graph = ForeignKeyGraphBuilder.from_reconstruction(recon)

    assert graph.node_count == 2
    assert graph.edge_count == 1
    edge = graph.edges[0]
    assert edge.is_composite is True
    assert len(edge.column_pairs) == 2


def test_full_pipeline_self_referencing():
    canonical_db = make_self_referencing_schema()
    schema = SchemaBuilder.from_canonical_database(canonical_db)
    recon = StructuralReconstructionBuilder().build_from_schema(schema)
    graph = ForeignKeyGraphBuilder.from_reconstruction(recon)

    assert graph.node_count == 1
    assert graph.edge_count == 1
    edge = graph.edges[0]
    assert edge.is_self_referencing is True


def test_full_pipeline_parallel_edges():
    canonical_db = make_parallel_edges_schema()
    schema = SchemaBuilder.from_canonical_database(canonical_db)
    recon = StructuralReconstructionBuilder().build_from_schema(schema)
    graph = ForeignKeyGraphBuilder.from_reconstruction(recon)

    assert graph.node_count == 2
    assert graph.edge_count == 2
