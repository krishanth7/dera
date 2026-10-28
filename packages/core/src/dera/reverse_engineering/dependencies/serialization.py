"""DERA Reverse Engineering — Phase 6.4 Dependency Serialization.

Provides canonical RFC 8785 JSON serialization, size limit enforcement, and SHA-256
cryptographic fingerprinting for DependencyAnalysisResult contracts.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from dera.reverse_engineering.dependencies.errors import (
    DependencyResourceLimitError,
    DependencySerializationError,
)
from dera.reverse_engineering.dependencies.limits import DependencyResourceLimits
from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult


def serialize_dependency_analysis_to_dict(
    result: DependencyAnalysisResult,
) -> dict[str, Any]:
    """Serialize DependencyAnalysisResult to a plain Python dictionary."""
    return result.model_dump(mode="json")


def serialize_dependency_analysis_to_json(
    result: DependencyAnalysisResult,
    limits: DependencyResourceLimits | None = None,
) -> str:
    """Serialize DependencyAnalysisResult to canonical RFC 8785 sorted JSON.

    Args:
        result: The DependencyAnalysisResult to serialize.
        limits: Optional resource limits to enforce maximum payload byte length.

    Returns:
        Canonical JSON string with sorted keys and compact separators.

    Raises:
        DependencyResourceLimitError: If serialized bytes exceed max_serialized_bytes.
    """
    effective_limits = limits or DependencyResourceLimits()
    data = serialize_dependency_analysis_to_dict(result)
    canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    encoded_bytes = len(canonical_json.encode("utf-8"))
    if encoded_bytes > effective_limits.max_serialized_bytes:
        raise DependencyResourceLimitError(
            f"Serialized dependency analysis payload ({encoded_bytes} bytes) exceeds configured "
            f"limit of {effective_limits.max_serialized_bytes} bytes."
        )

    return canonical_json


def deserialize_dependency_analysis_from_dict(
    data: dict[str, Any],
) -> DependencyAnalysisResult:
    """Deserialize DependencyAnalysisResult from a dictionary representation."""
    try:
        return DependencyAnalysisResult.model_validate(data)
    except Exception as exc:
        raise DependencySerializationError(
            f"Failed to deserialize DependencyAnalysisResult: {exc}"
        ) from exc


def deserialize_dependency_analysis_from_json(
    json_str: str,
) -> DependencyAnalysisResult:
    """Deserialize DependencyAnalysisResult from a JSON string."""
    try:
        data = json.loads(json_str)
        return deserialize_dependency_analysis_from_dict(data)
    except Exception as exc:
        raise DependencySerializationError(
            f"Failed to deserialize DependencyAnalysisResult from JSON: {exc}"
        ) from exc


def compute_dependency_hash(result: DependencyAnalysisResult) -> str:
    """Compute deterministic SHA-256 fingerprint over canonical JSON serialization."""
    canonical_json = serialize_dependency_analysis_to_json(result)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
