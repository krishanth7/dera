"""Tests for RFC 8785 JSON serialization, round-trip fidelity, and size limit enforcement."""

from __future__ import annotations

import pytest
from dera.reverse_engineering.dependencies.errors import DependencyResourceLimitError
from dera.reverse_engineering.dependencies.limits import DependencyResourceLimits
from dera.reverse_engineering.dependencies.serialization import (
    deserialize_dependency_analysis_from_dict,
    deserialize_dependency_analysis_from_json,
    serialize_dependency_analysis_to_dict,
    serialize_dependency_analysis_to_json,
)

from tests.reverse_engineering.phase_6_4.fixtures import (
    analyze_database,
    make_ecommerce_schema,
    make_mutual_cycle_schema,
)


def test_serialization_round_trip():
    """Verify that serialization to JSON and back produces identical DependencyAnalysisResult."""
    db = make_ecommerce_schema()
    original = analyze_database(db)

    json_str = serialize_dependency_analysis_to_json(original)
    recovered = deserialize_dependency_analysis_from_json(json_str)

    assert recovered.contract_version == original.contract_version
    assert recovered.is_dag == original.is_dag
    assert recovered.node_count == original.node_count
    assert recovered.edge_count == original.edge_count
    assert recovered.ordering.creation_order == original.ordering.creation_order
    assert recovered.ordering.drop_order == original.ordering.drop_order
    assert len(recovered.ordering.levels) == len(original.ordering.levels)
    assert recovered.compute_hash() == original.compute_hash()


def test_dict_serialization_round_trip():
    """Verify dict-level round-trip deserialization."""
    db = make_mutual_cycle_schema()
    original = analyze_database(db)

    data_dict = serialize_dependency_analysis_to_dict(original)
    recovered = deserialize_dependency_analysis_from_dict(data_dict)

    assert recovered.cycle_report.cycle_count == original.cycle_report.cycle_count
    assert recovered.compute_hash() == original.compute_hash()


def test_serialization_size_limit_enforcement():
    """Verify DependencyResourceLimitError is raised if payload exceeds max_serialized_bytes."""
    db = make_ecommerce_schema()
    res = analyze_database(db)

    # Tight limit of 1024 bytes (payload is ~4500 bytes)
    tight_limits = DependencyResourceLimits(max_serialized_bytes=1024)

    with pytest.raises(DependencyResourceLimitError):
        serialize_dependency_analysis_to_json(res, limits=tight_limits)
