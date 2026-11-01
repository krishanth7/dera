"""DERA Comparison — Phase 9.1 Fingerprint Computation.

Implements deterministic, collision-resistant SHA-256 fingerprints for
individual schema differences, comparison configurations, and the overall diff report.

Invariants:
- Volatile metadata (timestamps, process IDs, memory addresses, random UUIDs) is strictly excluded.
- Inputs are normalized via RFC 8785 canonical JSON serialization.
- Lowercase 64-character hexadecimal format.
"""

from __future__ import annotations

import hashlib
from typing import Any

from dera.comparison.serializers import dumps_canonical_bytes

DIFF_CHANGE_DOMAIN = "DERA:DIFF:CHANGE:V1\n"
DIFF_CONFIG_DOMAIN = "DERA:DIFF:CONFIG:V1\n"
DIFF_REPORT_DOMAIN = "DERA:DIFF:REPORT:V1\n"


def compute_change_fingerprint(
    comparator_version: str,
    object_type: str,
    canonical_id: str,
    change_type: str,
    before_properties: dict[str, Any] | None,
    after_properties: dict[str, Any] | None,
    changed_properties: tuple[str, ...],
) -> str:
    """Compute a reproducible SHA-256 fingerprint for a single schema change record."""
    payload = {
        "comparator_version": comparator_version,
        "object_type": str(object_type).upper(),
        "canonical_id": canonical_id,
        "change_type": str(change_type).upper(),
        "changed_properties": sorted(changed_properties),
        "before_properties": before_properties or {},
        "after_properties": after_properties or {},
    }
    canonical_bytes = dumps_canonical_bytes(payload)
    hasher = hashlib.sha256()
    hasher.update(DIFF_CHANGE_DOMAIN.encode("utf-8"))
    hasher.update(canonical_bytes)
    return hasher.hexdigest().lower()


def compute_configuration_fingerprint(config_dict: dict[str, Any]) -> str:
    """Compute a reproducible SHA-256 fingerprint for comparison configuration options."""
    canonical_bytes = dumps_canonical_bytes(config_dict)
    hasher = hashlib.sha256()
    hasher.update(DIFF_CONFIG_DOMAIN.encode("utf-8"))
    hasher.update(canonical_bytes)
    return hasher.hexdigest().lower()


def compute_report_fingerprint(
    baseline_fingerprint: str,
    target_fingerprint: str,
    config_fingerprint: str,
    change_fingerprints: tuple[str, ...],
) -> str:
    """Compute a reproducible SHA-256 fingerprint for the complete comparison report."""
    payload = {
        "baseline_fingerprint": baseline_fingerprint,
        "target_fingerprint": target_fingerprint,
        "config_fingerprint": config_fingerprint,
        "change_fingerprints": sorted(change_fingerprints),
    }
    canonical_bytes = dumps_canonical_bytes(payload)
    hasher = hashlib.sha256()
    hasher.update(DIFF_REPORT_DOMAIN.encode("utf-8"))
    hasher.update(canonical_bytes)
    return hasher.hexdigest().lower()
