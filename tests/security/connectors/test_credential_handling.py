"""Tests for Credential Management & Masking Safety.

Validates that database credentials are encapsulated, masked across repr and str,
and protected from null-byte corruption or diagnostic leakage.
"""

import unittest

from dera_connectors.security import (
    CredentialExposureError,
    DatabaseCredentials,
    SecureCredentialResolver,
    mask_sensitive_strings,
    redact_credentials,
)


class TestCredentialHandling(unittest.TestCase):
    """Test suite verifying credential protection invariants."""

    def test_database_credentials_repr_never_leaks_password(self) -> None:
        """Verify __repr__ and __str__ display '***' instead of the raw password."""
        creds = DatabaseCredentials(
            username="admin_user",
            password="UltraSecretPassword123!",
        )
        self.assertNotIn("UltraSecretPassword123!", repr(creds))
        self.assertNotIn("UltraSecretPassword123!", str(creds))
        self.assertIn("password='***'", repr(creds))
        # Raw password accessible only via explicit getter
        self.assertEqual(creds.expose_raw_password(), "UltraSecretPassword123!")

    def test_null_byte_in_credentials_rejected(self) -> None:
        """Verify credentials containing null bytes raise CredentialExposureError."""
        with self.assertRaises(CredentialExposureError):
            SecureCredentialResolver.resolve_from_dict(
                {
                    "username": "admin\0injection",
                    "password": "valid_password",
                }
            )

        with self.assertRaises(CredentialExposureError):
            SecureCredentialResolver.resolve_from_dict(
                {
                    "username": "admin",
                    "password": "pass\0word",
                }
            )

    def test_redact_credentials_scrubs_secrets(self) -> None:
        """Verify redact_credentials masks password and auth tokens."""
        raw_config = {
            "host": "db.internal.net",
            "port": 5432,
            "username": "svc_dera",
            "password": "MySuperSecretPassword!",
            "auth_token": "bearer-token-12345",
            "database": "analytics",
        }
        redacted = redact_credentials(raw_config)
        self.assertEqual(redacted["host"], "db.internal.net")
        self.assertEqual(redacted["username"], "svc_dera")
        self.assertEqual(redacted["password"], "***")
        self.assertEqual(redacted["auth_token"], "***")
        self.assertEqual(redacted["database"], "analytics")

    def test_mask_sensitive_strings_handles_various_formats(self) -> None:
        """Verify URL and key-value secret masking."""
        uri = "mysql://user:Secret123@db-host:3306/db"
        masked = mask_sensitive_strings(uri)
        self.assertNotIn("Secret123", masked)
        self.assertIn("mysql://user:***@db-host:3306/db", masked)

        raw_text = "Connection failure: api_key='ak_live_9988776655' on remote"
        masked_text = mask_sensitive_strings(raw_text)
        self.assertNotIn("ak_live_9988776655", masked_text)
        self.assertIn("api_key=***", masked_text)


if __name__ == "__main__":
    unittest.main()
