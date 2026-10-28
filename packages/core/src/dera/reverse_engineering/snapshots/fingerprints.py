"""DERA Reverse Engineering — Phase 6.5 Deterministic Cryptographic Fingerprinting.

Implements domain-separated SHA-256 content-based fingerprinting for schema snapshot structural payloads.

Guarantees:
- Domain separation prefix (DERA:SCHEMA:STRUCTURAL:V1) prevents cross-protocol hash collisions.
- Strictly bounds digest input to canonical structural payload bytes; excludes volatile envelope data.
- Reproducible across runtime invocations, platforms, and database connection instances.
- 64-character lowercase hexadecimal representation.
"""

from __future__ import annotations

import hashlib
import re

from dera.reverse_engineering.snapshots.limits import SnapshotResourceLimits
from dera.reverse_engineering.snapshots.models import (
    FINGERPRINT_DOMAIN,
    SchemaSnapshot,
    SnapshotStructuralPayload,
)
from dera.reverse_engineering.snapshots.serialization import (
    serialize_snapshot_to_json,
    serialize_structural_payload_to_bytes,
)

HEX_64_REGEX = re.compile(r"^[0-9a-f]{64}$")


def validate_fingerprint_format(fingerprint: str) -> bool:
    """Validate that a string is a 64-character lowercase hexadecimal SHA-256 digest."""
    if not isinstance(fingerprint, str):
        return False
    return bool(HEX_64_REGEX.match(fingerprint))


def compute_structural_fingerprint(
    payload: SnapshotStructuralPayload,
    limits: SnapshotResourceLimits | None = None,
) -> str:
    """Compute a deterministic, domain-separated SHA-256 fingerprint over a structural payload.

    Formula:
        SHA-256( b"DERA:SCHEMA:STRUCTURAL:V1\\n" + canonical_structural_payload_bytes )

    Args:
        payload: Canonical SnapshotStructuralPayload to fingerprint.
        limits: Optional resource limits.

    Returns:
        64-character lowercase hex digest string.
    """
    payload_bytes = serialize_structural_payload_to_bytes(payload, limits=limits)
    domain_header = f"{FINGERPRINT_DOMAIN}\n".encode()

    hasher = hashlib.sha256()
    hasher.update(domain_header)
    hasher.update(payload_bytes)
    return hasher.hexdigest().lower()


def compute_snapshot_envelope_hash(
    snapshot: SchemaSnapshot,
    limits: SnapshotResourceLimits | None = None,
) -> str:
    """Compute a SHA-256 digest over the entire canonical JSON serialization of a SchemaSnapshot.

    Used for physical storage integrity and tamper detection of the full record.
    """
    snapshot_json = serialize_snapshot_to_json(snapshot, indent=None, limits=limits)
    hasher = hashlib.sha256()
    hasher.update(b"DERA:SNAPSHOT:RECORD:V1\n")
    hasher.update(snapshot_json.encode("utf-8"))
    return hasher.hexdigest().lower()
