"""Tests for Cryptographic Token Generation and SHA-256 Hashing.

Validates session token entropy, SHA-256 hash determinism, CSRF token structure,
and constant-time string comparison.
"""

import unittest

from dera_api.auth.tokens import (
    constant_time_compare,
    generate_csrf_token,
    generate_session_token,
    hash_session_token,
)


class TestTokens(unittest.TestCase):
    """Test suite for session and CSRF token operations."""

    def test_session_token_entropy_and_format(self) -> None:
        """Verify that session tokens are 64 hex characters (32 bytes entropy)."""
        token1 = generate_session_token()
        token2 = generate_session_token()

        self.assertEqual(len(token1), 64)
        self.assertEqual(len(token2), 64)
        self.assertNotEqual(token1, token2)
        # Verify valid hex
        int(token1, 16)
        int(token2, 16)

    def test_hash_session_token_determinism(self) -> None:
        """Verify that hash_session_token produces a 64-char hex SHA-256 string deterministically."""
        token = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        hash1 = hash_session_token(token)
        hash2 = hash_session_token(token)

        self.assertEqual(len(hash1), 64)
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, token)

    def test_csrf_token_generation(self) -> None:
        """Verify that CSRF tokens are non-empty URL-safe strings with high entropy."""
        csrf1 = generate_csrf_token()
        csrf2 = generate_csrf_token()

        self.assertGreaterEqual(len(csrf1), 40)
        self.assertNotEqual(csrf1, csrf2)

    def test_constant_time_comparison(self) -> None:
        """Verify constant-time equality check behavior."""
        self.assertTrue(constant_time_compare("secret-value", "secret-value"))
        self.assertFalse(constant_time_compare("secret-value", "wrong-value"))
        self.assertFalse(constant_time_compare("secret", "secret-longer"))
        self.assertFalse(constant_time_compare(None, "val"))
        self.assertFalse(constant_time_compare("val", None))
        self.assertFalse(constant_time_compare(None, None))


if __name__ == "__main__":
    unittest.main()
