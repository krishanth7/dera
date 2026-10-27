"""DERA Auth — Cryptographic Token Generation and Storage Hashing.

Generates 256-bit cryptographically secure opaque session tokens, computes deterministic
SHA-256 hashes for PostgreSQL database persistence, and generates CSRF defense tokens.
"""

import hashlib
import hmac
import secrets


def generate_session_token() -> str:
    """Generate a 256-bit (32 bytes) cryptographically secure opaque session token.

    Returns a 64-character hex-encoded string.
    """
    return secrets.token_hex(32)


def hash_session_token(token: str) -> str:
    """Compute deterministic SHA-256 hash of an opaque session token.

    Only the hash is persisted in the PostgreSQL database; the raw token is returned
    to the client via HttpOnly cookie or Authorization header.
    """
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    """Generate a cryptographically secure random token for Double-Submit CSRF defense.

    Returns a URL-safe base64 string with at least 256 bits of entropy.
    """
    return secrets.token_urlsafe(32)


def constant_time_compare(val1: str | None, val2: str | None) -> bool:
    """Compare two string values in constant time to prevent timing side-channels."""
    if val1 is None or val2 is None:
        return False
    return hmac.compare_digest(val1.encode("utf-8"), val2.encode("utf-8"))
