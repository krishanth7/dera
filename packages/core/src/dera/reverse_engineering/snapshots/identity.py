"""DERA Reverse Engineering — Phase 6.5 Snapshot Identity.

Provides generation, validation, and typing for unique snapshot record identifiers.
Snapshot identifiers distinguish the capture envelope record from the content-based structural fingerprint.
"""

from __future__ import annotations

import re
import uuid

SNAPSHOT_ID_PREFIX = "snap_"
SNAPSHOT_ID_REGEX = re.compile(r"^snap_[0-9a-f]{32}$")


def generate_snapshot_id() -> str:
    """Generate a unique, URL-safe snapshot record identifier."""
    return f"{SNAPSHOT_ID_PREFIX}{uuid.uuid4().hex}"


def validate_snapshot_id(snapshot_id: str) -> bool:
    """Validate that a snapshot identifier conforms to the standard format."""
    if not isinstance(snapshot_id, str):
        return False
    return bool(SNAPSHOT_ID_REGEX.match(snapshot_id))
