"""Domain-separated SHA-256 using Phase 9 canonical serialization."""

from hashlib import sha256

from dera.comparison.serializers import dumps_canonical_bytes


def fingerprint(payload: dict) -> str:
    return sha256(b"DERA:SQL:DIAGNOSTICS:V1\n" + dumps_canonical_bytes(payload)).hexdigest()
