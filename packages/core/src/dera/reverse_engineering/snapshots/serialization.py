"""DERA Reverse Engineering — Phase 6.5 Deterministic Snapshot Serialization.

Provides RFC 8785 compliant canonical JSON serialization and safe deserialization
for SchemaSnapshot and SnapshotStructuralPayload instances.

Guarantees:
- Strict lexicographical key sorting at all nested dictionary levels.
- Compact separators (',' and ':') without extraneous whitespace for hashing.
- UTF-8 encoding with unescaped Unicode characters.
- Deterministic datetime formatting (RFC 3339 / ISO 8601 UTC ending in 'Z').
- Rejection of non-finite numbers (NaN, Infinity).
- Explicit null values.
- Enforced byte-size resource limits against DoS.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from typing import Any

from dera.reverse_engineering.snapshots.errors import (
    SnapshotDeserializationError,
    SnapshotError,
    SnapshotResourceLimitError,
    SnapshotSerializationError,
)
from dera.reverse_engineering.snapshots.limits import SnapshotResourceLimits
from dera.reverse_engineering.snapshots.models import (
    SchemaSnapshot,
    SnapshotStructuralPayload,
)


def _snapshot_default_serializer(obj: Any) -> Any:
    """Format non-standard types deterministically in canonical serialization."""
    if isinstance(obj, datetime):
        if obj.tzinfo is None:
            utc_dt = obj.replace(tzinfo=UTC)
        else:
            utc_dt = obj.astimezone(UTC)
        # Format as RFC 3339 UTC with 'Z'
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise SnapshotSerializationError(
                f"Non-finite float value '{obj}' is forbidden in canonical JSON."
            )
        return obj
    if hasattr(obj, "value"):  # Enums
        return obj.value
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _validate_numeric_values(data: Any) -> None:
    """Recursively verify no NaN or Infinite numeric values exist in serialization data."""
    if isinstance(data, dict):
        for v in data.values():
            _validate_numeric_values(v)
    elif isinstance(data, (list, tuple)):
        for item in data:
            _validate_numeric_values(item)
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            raise SnapshotSerializationError(
                f"Non-finite float value '{data}' is prohibited in snapshot serialization."
            )


def serialize_structural_payload_to_bytes(
    payload: SnapshotStructuralPayload,
    limits: SnapshotResourceLimits | None = None,
) -> bytes:
    """Serialize a SnapshotStructuralPayload to compact RFC 8785 canonical UTF-8 JSON bytes.

    Used directly as input to the cryptographic fingerprint digest.
    """
    effective_limits = limits or SnapshotResourceLimits()
    try:
        raw_dict = payload.model_dump(mode="json")
        _validate_numeric_values(raw_dict)
        canonical_str = json.dumps(
            raw_dict,
            indent=None,
            separators=(",", ":"),
            sort_keys=True,
            ensure_ascii=False,
            default=_snapshot_default_serializer,
        )
        canonical_bytes = canonical_str.encode("utf-8")
        if len(canonical_bytes) > effective_limits.max_serialized_bytes:
            raise SnapshotResourceLimitError(
                f"Serialized structural payload ({len(canonical_bytes)} bytes) exceeds limit "
                f"of {effective_limits.max_serialized_bytes} bytes."
            )
        return canonical_bytes
    except SnapshotError:
        raise
    except Exception as exc:
        raise SnapshotSerializationError(f"Failed to serialize structural payload: {exc}") from exc


def serialize_snapshot_to_json(
    snapshot: SchemaSnapshot,
    indent: int | None = None,
    limits: SnapshotResourceLimits | None = None,
) -> str:
    """Serialize a complete SchemaSnapshot to canonical JSON string."""
    effective_limits = limits or SnapshotResourceLimits()
    try:
        raw_dict = snapshot.model_dump(mode="json")
        _validate_numeric_values(raw_dict)
        separators = (",", ":") if indent is None else (",", ": ")
        json_str = json.dumps(
            raw_dict,
            indent=indent,
            separators=separators,
            sort_keys=True,
            ensure_ascii=False,
            default=_snapshot_default_serializer,
        )
        encoded_bytes = len(json_str.encode("utf-8"))
        if encoded_bytes > effective_limits.max_serialized_bytes:
            raise SnapshotResourceLimitError(
                f"Serialized snapshot ({encoded_bytes} bytes) exceeds limit of "
                f"{effective_limits.max_serialized_bytes} bytes."
            )
        return json_str
    except SnapshotError:
        raise
    except Exception as exc:
        raise SnapshotSerializationError(f"Failed to serialize snapshot: {exc}") from exc


def deserialize_snapshot_from_json(
    json_str: str,
    limits: SnapshotResourceLimits | None = None,
) -> SchemaSnapshot:
    """Safely reconstruct a SchemaSnapshot from a canonical JSON string without executing code."""
    effective_limits = limits or SnapshotResourceLimits()
    payload_len = len(json_str.encode("utf-8"))
    if payload_len > effective_limits.max_serialized_bytes:
        raise SnapshotResourceLimitError(
            f"Incoming payload ({payload_len} bytes) exceeds maximum allowed size of "
            f"{effective_limits.max_serialized_bytes} bytes."
        )

    try:
        raw_dict = json.loads(json_str)
        if not isinstance(raw_dict, dict):
            raise SnapshotDeserializationError("Root of snapshot JSON must be an object.")
        return SchemaSnapshot.model_validate(raw_dict)
    except SnapshotError:
        raise
    except Exception as exc:
        raise SnapshotDeserializationError(f"Failed to deserialize SchemaSnapshot: {exc}") from exc


def deserialize_structural_payload_from_json(
    json_str: str,
    limits: SnapshotResourceLimits | None = None,
) -> SnapshotStructuralPayload:
    """Safely reconstruct a SnapshotStructuralPayload from a canonical JSON string."""
    effective_limits = limits or SnapshotResourceLimits()
    payload_len = len(json_str.encode("utf-8"))
    if payload_len > effective_limits.max_serialized_bytes:
        raise SnapshotResourceLimitError(
            f"Incoming structural payload ({payload_len} bytes) exceeds limit of "
            f"{effective_limits.max_serialized_bytes} bytes."
        )

    try:
        raw_dict = json.loads(json_str)
        if not isinstance(raw_dict, dict):
            raise SnapshotDeserializationError("Root of structural payload JSON must be an object.")
        return SnapshotStructuralPayload.model_validate(raw_dict)
    except SnapshotError:
        raise
    except Exception as exc:
        raise SnapshotDeserializationError(
            f"Failed to deserialize SnapshotStructuralPayload: {exc}"
        ) from exc
