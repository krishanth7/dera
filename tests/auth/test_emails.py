"""Tests for Email Syntax Validation and Conservative Normalization.

Validates RFC 5321/5322 compliance, lowercase domain handling, dot and plus-tag preservation,
and rejection of invalid syntax or excessive length.
"""

import unittest

from dera_api.auth.email import EmailValidationError, normalize_email


class TestEmailNormalization(unittest.TestCase):
    """Test suite for email validation and conservative normalization."""

    def test_standard_normalization(self) -> None:
        """Verify trimming whitespace and lowercasing domain and local parts."""
        raw = "  Engineer@Example.COM  "
        normalized = normalize_email(raw)
        self.assertEqual(normalized, "engineer@example.com")

    def test_preserves_plus_addressing_tags(self) -> None:
        """Verify that sub-addressing (+tag) is strictly preserved and not stripped."""
        raw = "User+TestTag@Domain.COM"
        normalized = normalize_email(raw)
        self.assertEqual(normalized, "user+testtag@domain.com")

    def test_preserves_dots_in_localpart(self) -> None:
        """Verify that dots in the localpart are preserved without alias collapsing."""
        raw = "first.last.dev@example.org"
        normalized = normalize_email(raw)
        self.assertEqual(normalized, "first.last.dev@example.org")

    def test_rejects_invalid_syntax(self) -> None:
        """Verify that malformed email strings raise EmailValidationError."""
        invalid_emails = [
            "plainaddress",
            "@missinglocal.com",
            "missingdomain@",
            "missing-at-sign.com",
            "two@@at.com",
            "spaces in@local.com",
            "user@.starts-with-dot.com",
        ]
        for candidate in invalid_emails:
            with self.subTest(candidate=candidate):
                with self.assertRaises(EmailValidationError):
                    normalize_email(candidate)

    def test_rejects_excessive_lengths(self) -> None:
        """Verify length boundaries for total address (254) and local part (64)."""
        # Local part > 64 chars
        long_local = "a" * 65 + "@example.com"
        with self.assertRaises(EmailValidationError):
            normalize_email(long_local)

        # Total length > 254 chars
        long_domain = "a" * 200 + "." + "b" * 50 + ".com"
        too_long = f"user@{long_domain}"
        with self.assertRaises(EmailValidationError):
            normalize_email(too_long)


if __name__ == "__main__":
    unittest.main()
