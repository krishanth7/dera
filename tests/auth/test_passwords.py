"""Tests for Password Hashing and Policy Validation.

Validates Argon2id hashing, constant-time verification, NIST SP 800-63B length rules,
rejection of trivial compromised patterns, and hash rehash checks.
"""

import unittest

from dera_api.auth.password import (
    PasswordPolicyError,
    hash_password,
    validate_password_complexity,
    verify_hash_needs_rehash,
    verify_password,
)


class TestPasswordSecurity(unittest.TestCase):
    """Test suite for password hashing and policy enforcement."""

    def test_hash_and_verify_valid_password(self) -> None:
        """Verify that a valid password hashes cleanly with Argon2id and verifies."""
        pwd = "correct-horse-battery-staple-2026"
        hashed = hash_password(pwd)
        self.assertTrue(hashed.startswith("$argon2id$"))
        self.assertTrue(verify_password(pwd, hashed))

    def test_verify_invalid_password_returns_false(self) -> None:
        """Verify that incorrect candidate password returns False safely."""
        pwd = "correct-horse-battery-staple-2026"
        hashed = hash_password(pwd)
        self.assertFalse(verify_password("wrong-password-attempt", hashed))

    def test_verify_empty_or_malformed_hash(self) -> None:
        """Verify that malformed or empty inputs return False without crashing."""
        self.assertFalse(verify_password("", "some-hash"))
        self.assertFalse(verify_password("password", ""))
        self.assertFalse(verify_password("password", "invalid-hash-structure"))

    def test_password_length_constraints(self) -> None:
        """Verify minimum (12) and maximum (128) character length limits."""
        # Too short (<12)
        with self.assertRaises(PasswordPolicyError):
            validate_password_complexity("short123")

        # Boundary: 12 chars valid
        validate_password_complexity("validtwelve!")

        # Maximum length: 128 chars valid
        validate_password_complexity("a" * 128)

        # Exceeds maximum: >128 chars
        with self.assertRaises(PasswordPolicyError):
            validate_password_complexity("a" * 129)

    def test_whitespace_only_password_rejected(self) -> None:
        """Verify that whitespace-only passwords are rejected."""
        with self.assertRaises(PasswordPolicyError):
            validate_password_complexity("            ")

    def test_common_compromised_password_rejected(self) -> None:
        """Verify that known compromised passwords are rejected."""
        with self.assertRaises(PasswordPolicyError):
            validate_password_complexity("password123456")

        with self.assertRaises(PasswordPolicyError):
            validate_password_complexity("123456789012")

    def test_rehash_check(self) -> None:
        """Verify that freshly hashed password does not need rehashing."""
        pwd = "enterprise-strength-password-2026"
        hashed = hash_password(pwd)
        self.assertFalse(verify_hash_needs_rehash(hashed))


if __name__ == "__main__":
    unittest.main()
