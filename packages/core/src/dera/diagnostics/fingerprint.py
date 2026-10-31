"""DERA Diagnostics — Deterministic Fingerprint Generation.

Computes stable, cryptographic fingerprints for diagnostic findings and reports,
ensuring reproducibility without depending on volatile timestamps or system noise.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dera.diagnostics.evidence import DiagnosticEvidence


def _json_default(obj: Any) -> Any:
    """Fallback JSON serializer for standard types."""
    if hasattr(obj, "to_canonical_dict"):
        return obj.to_canonical_dict()
    if hasattr(obj, "value"):
        return obj.value
    if isinstance(obj, (set, frozenset)):
        return sorted(list(obj))
    return str(obj)


def compute_finding_fingerprint(
    rule_id: str,
    rule_version: str,
    object_id: str,
    evidence: tuple[DiagnosticEvidence, ...] | list[DiagnosticEvidence],
) -> str:
    """Computes a stable SHA-256 fingerprint for a diagnostic finding.

    Derivation components:
      1. rule_id (canonical identifier)
      2. rule_version (semantic rule version)
      3. object_id (canonical database object ID)
      4. Canonical serialization of sorted evidence tuples
    """
    sorted_evidence = sorted(
        [e.to_canonical_dict() for e in evidence],
        key=lambda d: (d["field_name"], str(d["observed_value"])),
    )

    fingerprint_payload = {
        "rule_id": rule_id,
        "rule_version": rule_version,
        "object_id": object_id,
        "evidence": sorted_evidence,
    }

    serialized = json.dumps(
        fingerprint_payload,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_config_fingerprint(config_dict: dict[str, Any]) -> str:
    """Computes a deterministic SHA-256 hash representing engine configuration."""
    serialized = json.dumps(
        config_dict,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
