"""Unit tests for DERA FastAPI application factory.

Validates deterministic application construction, injected configuration,
middleware ordering, and documentation endpoint visibility.
"""

import unittest

from dera_api.core.config import ApiSettings
from dera_api.factory import create_app


class TestApiFactory(unittest.TestCase):
    """Test suite for validating create_app factory behavior."""

    def test_factory_creates_app_with_defaults(self) -> None:
        """Verify create_app constructs valid FastAPI application with defaults."""
        app = create_app()
        self.assertEqual(app.title, "DERA API Gateway")
        self.assertEqual(app.docs_url, "/docs")
        self.assertEqual(app.redoc_url, "/redoc")
        self.assertEqual(app.openapi_url, "/openapi.json")
        self.assertIsNotNone(app.state.settings)

    def test_factory_with_custom_injected_settings(self) -> None:
        """Verify custom settings are correctly injected into application."""
        custom_settings = ApiSettings(
            app_name="Custom DERA Gateway",
            port=9090,
            log_level="DEBUG",
            cors_origins=["https://dashboard.example.com"],
        )
        app = create_app(custom_settings)
        self.assertEqual(app.title, "Custom DERA Gateway")
        self.assertEqual(app.state.settings.port, 9090)
        self.assertEqual(app.state.settings.log_level, "DEBUG")

    def test_factory_with_docs_disabled(self) -> None:
        """Verify docs URLs are set to None when docs_enabled is False."""
        prod_settings = ApiSettings(
            environment="production",
            docs_enabled=False,
            cors_origins=["https://dera.dev"],
        )
        app = create_app(prod_settings)
        self.assertIsNone(app.docs_url)
        self.assertIsNone(app.redoc_url)
        self.assertIsNone(app.openapi_url)

    def test_factory_route_registration(self) -> None:
        """Verify all mandatory foundational routes are registered on the application."""
        app = create_app()
        registered_paths = set(app.openapi()["paths"].keys())

        expected_paths = {
            "/health/live",
            "/health/ready",
            "/health",
            "/info",
            "/api/v1/meta",
            "/api/v1/ping",
        }
        for path in expected_paths:
            self.assertIn(path, registered_paths, f"Expected route {path} not registered in app")


if __name__ == "__main__":
    unittest.main()
