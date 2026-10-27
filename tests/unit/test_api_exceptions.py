"""Unit tests for DERA API exception handling and information leak prevention.

Validates that errors return structured JSON payloads with correlation IDs,
preserving status codes while never exposing Python tracebacks or secrets.
"""

import unittest

from dera_api.core.exceptions import DeraConfigurationError, DeraError
from dera_api.factory import create_app
from fastapi import APIRouter
from fastapi.testclient import TestClient


class TestApiExceptions(unittest.TestCase):
    """Test suite for validating exception sanitization and error schemas."""

    def setUp(self) -> None:
        self.app = create_app()

        # Add temporary test routes to trigger specific exceptions
        router = APIRouter(prefix="/test-errors")

        @router.get("/domain-error")
        def trigger_domain_error() -> None:
            raise DeraError("Custom domain failure occurred", code="DOMAIN_FAIL", status_code=400)

        @router.get("/config-error")
        def trigger_config_error() -> None:
            raise DeraConfigurationError("Missing required database configuration")

        @router.get("/unexpected-error")
        def trigger_unexpected_error() -> None:
            raise RuntimeError(
                "Database connection string secret: postgres://admin:secret123@host:5432/db"
            )

        self.app.include_router(router)
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_domain_error_response(self) -> None:
        """Verify DeraError returns clean structured JSON with status 400 and request ID."""
        response = self.client.get(
            "/test-errors/domain-error", headers={"X-Request-ID": "test-req-123"}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], "DOMAIN_FAIL")
        self.assertEqual(data["error"]["message"], "Custom domain failure occurred")
        self.assertEqual(data["error"]["request_id"], "test-req-123")

    def test_config_error_response(self) -> None:
        """Verify DeraConfigurationError returns status 500 without leaking stack traces."""
        response = self.client.get("/test-errors/config-error")
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data["error"]["code"], "CONFIG_ERROR")
        self.assertEqual(data["error"]["message"], "Missing required database configuration")

    def test_unexpected_error_sanitization(self) -> None:
        """Verify unexpected errors do not expose Python tracebacks or raw credentials."""
        response = self.client.get("/test-errors/unexpected-error")
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["code"], "INTERNAL_ERROR")
        self.assertEqual(data["error"]["code"], "INTERNAL_ERROR")
        self.assertEqual(
            data["error"]["message"],
            "An unexpected error occurred while processing the request.",
        )
        # Ensure credentials and raw error text are NOT leaked to client
        raw_text = response.text
        self.assertNotIn("secret123", raw_text)
        self.assertNotIn("Traceback", raw_text)
        self.assertNotIn("RuntimeError", raw_text)


if __name__ == "__main__":
    unittest.main()
