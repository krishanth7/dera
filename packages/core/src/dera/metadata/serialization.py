"""DERA Canonical Metadata Normalization & Identity — Serialization.

Provides byte-level deterministic, canonical JSON serialization and SHA-256
fingerprint generation for CanonicalDatabase snapshots.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from dera.metadata.models.database import CanonicalDatabase


def _canonical_default_serializer(obj: Any) -> Any:
    """Format non-standard types deterministically."""
    if isinstance(obj, datetime):
        # Format as RFC 3339 / ISO 8601 UTC with explicit 'Z'
        utc_dt = obj.astimezone() if obj.tzinfo is not None else obj
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if hasattr(obj, "value"):  # Enums
        return obj.value
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def serialize_canonical_database(
    database: CanonicalDatabase,
    indent: int | None = 2,
) -> str:
    """Serialize CanonicalDatabase to deterministic UTF-8 JSON string.

    Guarantees:
    - Sorted keys (`sort_keys=True`).
    - Explicit null representation for empty fields.
    - Deterministic date/time formatting.
    - Predictable spacing (2-space indent or compact if indent=None).
    """
    raw_dict = database.model_dump(mode="json")
    return json.dumps(
        raw_dict,
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
        default=_canonical_default_serializer,
    )


def compute_canonical_database_hash(database: CanonicalDatabase) -> str:
    """Compute a deterministic SHA-256 fingerprint over the canonical JSON bytes.

    Compact serialization (no indentation, sorted keys) is hashed to provide
    a stable, reproducible digest invariant to formatting whitespace.
    """
    compact_json = json.dumps(
        database.model_dump(mode="json"),
        indent=None,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
        default=_canonical_default_serializer,
    )
    return hashlib.sha256(compact_json.encode("utf-8")).hexdigest()
