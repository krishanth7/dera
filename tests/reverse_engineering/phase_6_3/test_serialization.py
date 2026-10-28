"""Tests for deterministic JSON serialization, deserialization, and payload size bounds."""

from __future__ import annotations

import json

import pytest
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.errors import (
    GraphResourceLimitError,
    GraphSerializationError,
)
from dera.reverse_engineering.graph.limits import GraphResourceLimits
from dera.reverse_engineering.graph.serialization import (
    FOREIGN_KEY_GRAPH_CONTRACT_VERSION,
    deserialize_graph_from_json,
    serialize_graph_to_dict,
    serialize_graph_to_json,
)

from tests.reverse_engineering.phase_6_3.fixtures import (
    make_composite_fk_schema,
    make_simple_fk_schema,
)


def test_roundtrip_serialization():
    """Verify serialize -> deserialize -> serialize produces identical bytes and hashes."""
    db = make_composite_fk_schema()
    g1 = ForeignKeyGraphBuilder.from_canonical(db)

    json_str = serialize_graph_to_json(g1, indent=2)
    g2 = deserialize_graph_from_json(json_str)

    assert g1.compute_hash() == g2.compute_hash()
    assert g1.node_count == g2.node_count
    assert g1.edge_count == g2.edge_count
    assert g1.contract_version == FOREIGN_KEY_GRAPH_CONTRACT_VERSION


def test_serialization_enforces_payload_limits():
    """Verify deserialization rejects payloads exceeding max_serialized_bytes."""
    db = make_simple_fk_schema()
    g = ForeignKeyGraphBuilder.from_canonical(db)
    json_str = serialize_graph_to_json(g)

    # Artificially low limit
    tiny_limits = GraphResourceLimits(max_serialized_bytes=50)
    with pytest.raises(GraphResourceLimitError, match="max_serialized_bytes"):
        deserialize_graph_from_json(json_str, limits=tiny_limits)


def test_deserialization_rejects_malformed_json():
    with pytest.raises(GraphSerializationError, match="Malformed JSON payload"):
        deserialize_graph_from_json("not-a-json-string{}}")


def test_deserialization_rejects_unsupported_contract_version():
    db = make_simple_fk_schema()
    g = ForeignKeyGraphBuilder.from_canonical(db)
    raw_dict = serialize_graph_to_dict(g)
    raw_dict["contract_version"] = "99.0.0"
    tampered_json = json.dumps(raw_dict)

    with pytest.raises(
        GraphSerializationError, match="Unsupported foreign key graph contract version"
    ):
        deserialize_graph_from_json(tampered_json)
