"""DERA Auth — Password Hashing and Policy Validation.

Implements NIST SP 800-63B and OWASP ASVS compliant password handling using Argon2id.
Enforces configurable work parameters, constant-time verification, length limits (12-128 chars),
and rejection of common trivial passwords without arbitrary composition rules.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Pre-compiled list of common compromised passwords for offline rejection
COMMON_COMPROMISED_PASSWORDS: frozenset[str] = frozenset(
    {
        "password123456",
        "123456789012",
        "qwertyuiop12",
        "adminadmin12",
        "letmein12345",
        "welcome12345",
        "changeme1234",
        "iloveyou1234",
        "supersecret1",
        "deraadmin123",
    }
)

# Argon2id hasher using RFC 9106 recommended parameters
# memory_cost=19456 (19 MiB), time_cost=2, parallelism=1
_HASHER = PasswordHasher(
    time_cost=2,
    memory_cost=19456,
    parallelism=1,
    hash_len=32,
    salt_len=16,
)


class PasswordPolicyError(ValueError):
    """Raised when a candidate password violates NIST SP 800-63B guidelines."""


def validate_password_complexity(password: str) -> None:
    """Validate candidate password against NIST SP 800-63B guidelines.

    Rules:
    - Minimum length: 12 characters.
    - Maximum length: 128 characters (prevents CPU exhaustion on large inputs).
    - No whitespace-only strings.
    - Rejection of common compromised trivial patterns.
    - No arbitrary character composition requirements (allows password managers).
    """
    if not isinstance(password, str):
        raise PasswordPolicyError("Password must be a valid string.")

    length = len(password)
    if length < 12:
        raise PasswordPolicyError("Password must be at least 12 characters in length.")
    if length > 128:
        raise PasswordPolicyError("Password must not exceed 128 characters.")
    if not password.strip():
        raise PasswordPolicyError("Password cannot consist solely of whitespace characters.")

    if password.lower() in COMMON_COMPROMISED_PASSWORDS:
        raise PasswordPolicyError("The selected password is known to be easily compromised.")


def hash_password(password: str) -> str:
    """Hash a password using Argon2id with unique salt and RFC 9106 parameters.

    Validates password complexity before hashing.
    """
    validate_password_complexity(password)
    return _HASHER.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a candidate password against an Argon2id hash in constant time.

    Returns False safely on any hash format or verification failure without leaking internals.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return _HASHER.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError, VerificationError):
        return False
    except Exception:
        return False


def verify_hash_needs_rehash(hashed_password: str) -> bool:
    """Check if the stored hash was created with older Argon2 parameters and should be upgraded."""
    try:
        return _HASHER.check_needs_rehash(hashed_password)
    except Exception:
        return False
