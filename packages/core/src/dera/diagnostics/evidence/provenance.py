"""DERA Diagnostics — Evidence Provenance Tracking.

Constructs verifiable provenance records linking diagnostic evidence to source engines,
snapshots, inspection timestamps, and connector capabilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.diagnostics.evidence.models import EvidenceProvenance

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


def create_evidence_provenance(
    object_id: str,
    context: DiagnosticContext | None,
    capability_state: str | None = None,
) -> EvidenceProvenance:
    """Creates a deterministic EvidenceProvenance instance from the diagnostic context."""
    source_engine = "unknown"
    snapshot_id = None

    if context is not None:
        source_engine = context.source_engine or "unknown"
        snapshot_id = context.snapshot_id

    return EvidenceProvenance(
        source_engine=source_engine,
        connector_version="1.0.0",
        snapshot_id=snapshot_id,
        canonical_object_id=object_id,
        capability_state=capability_state,
    )
