"""DERA Reverse Engineering — Phase 6.3 Deterministic Graph Serialization.

Provides canonical byte-level JSON serialization, SHA-256 fingerprinting, and safe
reconstruction for ForeignKeyGraph instances.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

from dera.metadata.serialization import _canonical_default_serializer
from dera.reverse_engineering.graph.errors import (
    GraphResourceLimitError,
    GraphSerializationError,
)
from dera.reverse_engineering.graph.limits import GraphResourceLimits
from dera.reverse_engineering.graph.validation import ValidationMode, validate_foreign_key_graph

if TYPE_CHECKING:
    from dera.reverse_engineering.graph.models import ForeignKeyGraph

FOREIGN_KEY_GRAPH_CONTRACT_VERSION: str = "1.0.0"


def serialize_graph_to_dict(graph: ForeignKeyGraph) -> dict[str, Any]:
    """Serialize ForeignKeyGraph to a JSON-compatible dictionary."""
    try:
        return graph.model_dump(mode="json")
    except Exception as exc:
        raise GraphSerializationError(f"Failed to dump graph model: {exc}") from exc


def serialize_graph_to_json(
    graph: ForeignKeyGraph,
    indent: int | None = None,
) -> str:
    """Serialize ForeignKeyGraph to deterministic UTF-8 JSON.

    Guarantees:
    - Sorted dictionary keys at all levels (`sort_keys=True`).
    - Standard ISO 8601 UTC dates.
    - Explicit null representation for empty fields.
    - Zero execution logic or embedded credentials.
    - Deterministic across python runtimes.
    """
    try:
        raw_dict = serialize_graph_to_dict(graph)
        return json.dumps(
            raw_dict,
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
            default=_canonical_default_serializer,
        )
    except Exception as exc:
        raise GraphSerializationError(f"Failed to serialize foreign key graph: {exc}") from exc


def compute_graph_hash(graph: ForeignKeyGraph) -> str:
    """Compute a deterministic SHA-256 fingerprint over compact canonical JSON bytes.

    Digests are stable across runtime executions and invariant to formatting whitespace.
    """
    try:
        compact_json = json.dumps(
            serialize_graph_to_dict(graph),
            indent=None,
            separators=(",", ":"),
            sort_keys=True,
            ensure_ascii=False,
            default=_canonical_default_serializer,
        )
        return hashlib.sha256(compact_json.encode("utf-8")).hexdigest()
    except Exception as exc:
        raise GraphSerializationError(f"Failed to compute graph hash: {exc}") from exc


def deserialize_graph_from_dict(
    data: dict[str, Any],
    limits: GraphResourceLimits | None = None,
    mode: ValidationMode = ValidationMode.PERMISSIVE,
) -> ForeignKeyGraph:
    """Reconstruct a ForeignKeyGraph safely from a deserialized dictionary."""
    from dera.reverse_engineering.graph.models import ForeignKeyGraph

    effective_limits = limits or GraphResourceLimits()

    if not isinstance(data, dict):
        raise GraphSerializationError("Serialized graph payload must be a JSON object dictionary.")

    contract_version = data.get("contract_version")
    if contract_version != FOREIGN_KEY_GRAPH_CONTRACT_VERSION:
        raise GraphSerializationError(
            f"Unsupported foreign key graph contract version: {contract_version!r}. "
            f"Expected: {FOREIGN_KEY_GRAPH_CONTRACT_VERSION!r}."
        )

    # Validate resource limits
    nodes_data = data.get("nodes", [])
    if len(nodes_data) > effective_limits.max_nodes:
        raise GraphResourceLimitError("max_nodes", effective_limits.max_nodes, len(nodes_data))

    edges_data = data.get("edges", [])
    if len(edges_data) > effective_limits.max_edges:
        raise GraphResourceLimitError("max_edges", effective_limits.max_edges, len(edges_data))

    try:
        graph = ForeignKeyGraph.model_validate(data)
    except Exception as exc:
        raise GraphSerializationError(f"Malformed graph model data: {exc}") from exc

    # Validate graph integrity if requested
    validate_foreign_key_graph(
        nodes=graph.nodes,
        edges=graph.edges,
        adjacency=graph.get_adjacency(),
        workspace_id=graph.workspace_id,
        mode=mode,
    )

    return graph


def deserialize_graph_from_json(
    json_str: str,
    limits: GraphResourceLimits | None = None,
    mode: ValidationMode = ValidationMode.PERMISSIVE,
) -> ForeignKeyGraph:
    """Reconstruct a ForeignKeyGraph from a serialized JSON string.

    Enforces payload size limits and disallows executable deserialization.
    """
    effective_limits = limits or GraphResourceLimits()
    payload_bytes = len(json_str.encode("utf-8"))
    if payload_bytes > effective_limits.max_serialized_bytes:
        raise GraphResourceLimitError(
            "max_serialized_bytes",
            effective_limits.max_serialized_bytes,
            payload_bytes,
        )

    try:
        data = json.loads(json_str)
    except Exception as exc:
        raise GraphSerializationError(f"Malformed JSON payload: {exc}") from exc

    return deserialize_graph_from_dict(data, limits=effective_limits, mode=mode)
