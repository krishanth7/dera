"""DERA Comparison — Phase 9.1 Deterministic Serialization.

Implements RFC 8785 compliant canonical JSON serialization for comparison models,
ensuring sorted keys, compact formatting, unescaped UTF-8, and float/int validation.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from typing import Any

from dera.comparison.errors import ComparisonError


def _comparison_default_serializer(obj: Any) -> Any:
    """Format non-standard types deterministically in canonical serialization."""
    if isinstance(obj, datetime):
        utc_dt = obj.replace(tzinfo=UTC) if obj.tzinfo is None else obj.astimezone(UTC)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise ComparisonError(f"Non-finite float value '{obj}' is forbidden in canonical JSON.")
        return obj
    if hasattr(obj, "value"):  # Enums
        return obj.value
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _validate_numeric_values(data: Any) -> None:
    """Recursively verify no NaN or Infinite numeric values exist in data."""
    if isinstance(data, dict):
        for v in data.values():
            _validate_numeric_values(v)
    elif isinstance(data, (list, tuple)):
        for item in data:
            _validate_numeric_values(item)
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            raise ComparisonError(
                f"Non-finite float value '{data}' is prohibited in canonical JSON."
            )


def dumps_canonical_json(data: Any, indent: int | None = None) -> str:
    """Serialize arbitrary data to deterministic canonical JSON adhering to RFC 8785 conventions.

    Args:
        data: Python dict, list, primitive, or Pydantic model.
        indent: Optional indentation for human-readable output (None for canonical hashing).

    Returns:
        Deterministic JSON string.
    """
    _validate_numeric_values(data)
    separators = (", ", ": ") if indent is not None else (",", ":")
    return json.dumps(
        data,
        indent=indent,
        separators=separators,
        sort_keys=True,
        ensure_ascii=False,
        default=_comparison_default_serializer,
    )


def dumps_canonical_bytes(data: Any) -> bytes:
    """Serialize data to UTF-8 encoded compact RFC 8785 canonical bytes."""
    return dumps_canonical_json(data, indent=None).encode("utf-8")
