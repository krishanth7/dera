"""DERA Canonical Metadata Normalization & Identity — Capability Awareness.

Integrates with Phase 5.1 connector capability models to assess completeness,
visibility restrictions, and engine-specific unsupported catalog features.
"""

from __future__ import annotations

from typing import Any

from dera.metadata.enums import MetadataCompleteness


def assess_engine_metadata_completeness(
    engine: str,
    feature_name: str,
    capabilities: dict[str, Any] | None = None,
) -> MetadataCompleteness:
    """Evaluate metadata completeness status given engine capabilities.

    Distinguishes:
    - COMPLETE: Engine supports and exposes full catalog metadata.
    - PARTIAL: Engine exposes partial representation (e.g. SQLite unnamed check constraints).
    - RESTRICTED: Engine catalog exists but user account lacks inspection privileges.
    - UNSUPPORTED: Engine does not support or catalog this capability (e.g. stored routines in SQLite).
    """
    eng = engine.strip().lower()

    if capabilities is None:
        capabilities = {}

    status = capabilities.get(feature_name)
    if status is not None:
        status_str = str(status).lower()
        if "unsupported" in status_str:
            return MetadataCompleteness.UNSUPPORTED
        if "restricted" in status_str or "denied" in status_str:
            return MetadataCompleteness.RESTRICTED
        if "partial" in status_str:
            return MetadataCompleteness.PARTIAL
        if "supported" in status_str:
            return MetadataCompleteness.COMPLETE

    # Engine-specific fallback heuristics
    if eng == "sqlite":
        if feature_name in ("check_constraints_named", "stored_procedures", "alter_column"):
            return MetadataCompleteness.UNSUPPORTED
        if feature_name in ("check_constraints", "expression_indexes"):
            return MetadataCompleteness.PARTIAL

    return MetadataCompleteness.COMPLETE
