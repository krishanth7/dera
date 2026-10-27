"""Unit tests for DERA API typed configuration and profiles.

Validates environment profiles, port constraints, debug safety,
CORS origin parsing, and cached singleton behavior.
"""

import unittest

from dera_api.core.config import ApiSettings, clear_settings_cache, get_settings
from pydantic import ValidationError


class TestApiConfig(unittest.TestCase):
    """Test suite for validating ApiSettings configuration models."""

    def tearDown(self) -> None:
        clear_settings_cache()

    def test_default_settings(self) -> None:
        """Verify default configuration attributes and deterministic defaults."""
        settings = ApiSettings()
        self.assertEqual(settings.app_name, "DERA API Gateway")
        self.assertEqual(settings.environment, "development")
        self.assertFalse(settings.debug)
        self.assertEqual(settings.port, 8000)
        self.assertEqual(settings.log_level, "INFO")
        self.assertEqual(settings.api_prefix, "/api/v1")
        self.assertTrue(settings.docs_enabled)
        self.assertTrue(settings.read_only_enforced)
        self.assertTrue(settings.zero_ai_policy_enforced)

    def test_valid_environment_profiles(self) -> None:
        """Verify accepted environment profiles in varying casing."""
        for env in ["development", "testing", "production", "DEVELOPMENT", "Testing"]:
            settings = ApiSettings(environment=env)
            self.assertEqual(settings.environment, env.strip().lower())

    def test_invalid_environment_profile(self) -> None:
        """Verify rejection of unapproved environment names."""
        with self.assertRaises(ValidationError) as ctx:
            ApiSettings(environment="staging_unknown")
        self.assertIn("Invalid environment", str(ctx.exception))

    def test_port_boundaries(self) -> None:
        """Verify port must be strictly between 1 and 65535."""
        valid_ports = [1, 80, 443, 8000, 65535]
        for p in valid_ports:
            settings = ApiSettings(port=p)
            self.assertEqual(settings.port, p)

        invalid_ports = [0, -1, 65536, 100000]
        for p in invalid_ports:
            with self.assertRaises(ValidationError) as ctx:
                ApiSettings(port=p)
            self.assertIn("Port must be between 1 and 65535", str(ctx.exception))

    def test_log_levels(self) -> None:
        """Verify accepted log levels and rejection of invalid values."""
        for lvl in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "info", "debug"]:
            settings = ApiSettings(log_level=lvl)
            self.assertEqual(settings.log_level, lvl.upper())

        with self.assertRaises(ValidationError) as ctx:
            ApiSettings(log_level="VERBOSE")
        self.assertIn("Invalid log level", str(ctx.exception))

    def test_production_debug_forbidden(self) -> None:
        """Verify that enabling debug mode in production environment is strictly prohibited."""
        with self.assertRaises(ValidationError) as ctx:
            ApiSettings(environment="production", debug=True)
        self.assertIn("Debug mode is strictly prohibited in production", str(ctx.exception))

    def test_production_wildcard_cors_forbidden(self) -> None:
        """Verify that wildcard CORS origins in production environment are strictly prohibited."""
        with self.assertRaises(ValidationError) as ctx:
            ApiSettings(environment="production", cors_origins=["*"])
        self.assertIn("Wildcard CORS origins", str(ctx.exception))

    def test_cors_origins_parsing(self) -> None:
        """Verify comma-separated string parsing and list handling for CORS origins."""
        settings = ApiSettings(
            cors_origins="https://app.dera.dev, https://console.dera.dev"  # type: ignore[arg-type]
        )
        self.assertEqual(
            settings.cors_origins,
            ["https://app.dera.dev", "https://console.dera.dev"],
        )

    def test_docs_enabled_defaults(self) -> None:
        """Verify docs_enabled defaults to True in dev/test and False in production."""
        dev_settings = ApiSettings(environment="development")
        self.assertTrue(dev_settings.docs_enabled)

        test_settings = ApiSettings(environment="testing")
        self.assertTrue(test_settings.docs_enabled)

        prod_settings = ApiSettings(
            environment="production",
            cors_origins=["https://console.dera.dev"],
        )
        self.assertFalse(prod_settings.docs_enabled)

        explicit_prod = ApiSettings(
            environment="production",
            docs_enabled=True,
            cors_origins=["https://console.dera.dev"],
        )
        self.assertTrue(explicit_prod.docs_enabled)

    def test_cached_singleton_and_invalidation(self) -> None:
        """Verify get_settings returns cached instance and clear_settings_cache resets it."""
        s1 = get_settings()
        s2 = get_settings()
        self.assertIs(s1, s2)
        clear_settings_cache()
        s3 = get_settings()
        self.assertIsNot(s1, s3)


if __name__ == "__main__":
    unittest.main()
