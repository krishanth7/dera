"""DERA Reverse Engineering — Phase 6.5 Snapshot Compatibility & Equivalence.

Defines version support boundaries, format compatibility checks, and multi-tier
schema equivalence classifications (byte-identical, fingerprint match, none).
"""

from __future__ import annotations

from enum import StrEnum

from dera.reverse_engineering.snapshots.models import (
    SNAPSHOT_FORMAT_VERSION,
    SchemaSnapshot,
)
from dera.reverse_engineering.snapshots.serialization import (
    serialize_snapshot_to_json,
)

SUPPORTED_SNAPSHOT_FORMAT_VERSIONS: frozenset[str] = frozenset(
    [
        SNAPSHOT_FORMAT_VERSION,
        "1.0.0",
    ]
)


class EquivalenceLevel(StrEnum):
    """Classification of equivalence between two schema snapshots."""

    EXACT_BYTE_IDENTICAL = "exact_byte_identical"
    STRUCTURAL_FINGERPRINT_MATCH = "structural_fingerprint_match"
    NONE = "none"


class SnapshotCompatibilityChecker:
    """Evaluates format versions and structural equivalence between snapshots."""

    @staticmethod
    def is_version_supported(version: str) -> bool:
        """Check whether a snapshot format version string is supported."""
        return version in SUPPORTED_SNAPSHOT_FORMAT_VERSIONS

    @staticmethod
    def compare_snapshots(a: SchemaSnapshot, b: SchemaSnapshot) -> EquivalenceLevel:
        """Determine the level of equivalence between two snapshots.

        Equivalence Levels:
        - EXACT_BYTE_IDENTICAL: Byte-identical canonical JSON serialization across both structural payload and envelope.
        - STRUCTURAL_FINGERPRINT_MATCH: Matching structural fingerprints (identical database structure, even if capture times or snapshot IDs differ).
        - NONE: Distinct schema structures.
        """
        # Check structural fingerprint match
        if (
            a.fingerprint == b.fingerprint
            and a.fingerprint_domain == b.fingerprint_domain
            and a.fingerprint_algorithm == b.fingerprint_algorithm
        ):
            # Check if envelope and full JSON are also byte-identical
            json_a = serialize_snapshot_to_json(a, indent=None)
            json_b = serialize_snapshot_to_json(b, indent=None)
            if json_a == json_b:
                return EquivalenceLevel.EXACT_BYTE_IDENTICAL
            return EquivalenceLevel.STRUCTURAL_FINGERPRINT_MATCH

        return EquivalenceLevel.NONE
