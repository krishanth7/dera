"""Integration tests for DERA FastAPI application gateway.

Validates end-to-end HTTP request processing, liveness and readiness probes,
CORS policies, request correlation tracking, and security headers.
"""

import unittest

from dera_api.core.config import ApiSettings
from dera_api.factory import create_app
from fastapi.testclient import TestClient


class TestApiIntegration(unittest.TestCase):
    """Integration test suite for DERA API gateway endpoints and HTTP pipeline."""

    def setUp(self) -> None:
        self.settings = ApiSettings(
            app_name="DERA Integration Gateway",
            environment="testing",
            cors_origins=["http://localhost:3000", "https://console.dera.dev"],
        )
        self.app = create_app(self.settings)
        self.client_ctx = TestClient(self.app)
        self.client = self.client_ctx.__enter__()

    def tearDown(self) -> None:
        self.client_ctx.__exit__(None, None, None)

    def test_liveness_endpoint(self) -> None:
        """Verify GET /health/live returns HTTP 200 with status ok."""
        response = self.client.get("/health/live")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "dera-api")
        self.assertEqual(data["version"], self.settings.version)

    def test_readiness_endpoint(self) -> None:
        """Verify GET /health/ready returns HTTP 200 with truthful subsystem diagnostics."""
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["ready"])
        self.assertIn("subsystems", data)
        self.assertEqual(
            data["subsystems"]["application_state"],
            "operational",
        )
        self.assertEqual(
            data["subsystems"]["database_connectors"],
            "none_required_in_phase_4_1",
        )

    def test_legacy_health_and_info(self) -> None:
        """Verify legacy /health and /info backward-compatible routes."""
        health_resp = self.client.get("/health")
        self.assertEqual(health_resp.status_code, 200)
        self.assertEqual(health_resp.json()["status"], "healthy")

        info_resp = self.client.get("/info")
        self.assertEqual(info_resp.status_code, 200)
        info_data = info_resp.json()
        self.assertEqual(info_data["project"], "DERA")
        self.assertEqual(info_data["maintainer"], "Krishanth")
        self.assertIn("Deterministic", info_data["philosophy"])

    def test_api_v1_meta_and_ping(self) -> None:
        """Verify /api/v1/meta capabilities and /api/v1/ping heartbeat."""
        meta_resp = self.client.get("/api/v1/meta")
        self.assertEqual(meta_resp.status_code, 200)
        meta_data = meta_resp.json()
        self.assertEqual(meta_data["name"], "DERA Integration Gateway")
        self.assertTrue(meta_data["zero_ai_policy"])
        self.assertTrue(meta_data["read_only_enforced"])
        self.assertIn("sqlite", meta_data["supported_dialects"])

        ping_resp = self.client.get("/api/v1/ping")
        self.assertEqual(ping_resp.status_code, 200)
        ping_data = ping_resp.json()
        self.assertEqual(ping_data["ping"], "pong")
        self.assertIn("timestamp", ping_data)

    def test_request_id_generation_and_propagation(self) -> None:
        """Verify automatic generation of X-Request-ID when not provided by client."""
        response = self.client.get("/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertIn("x-request-id", response.headers)
        request_id = response.headers["x-request-id"]
        self.assertGreater(len(request_id), 10)

    def test_request_id_valid_custom_propagation(self) -> None:
        """Verify valid client-supplied correlation ID is preserved and echoed."""
        custom_id = "req-audit-trace-9999"
        response = self.client.get("/health/live", headers={"X-Request-ID": custom_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-request-id"), custom_id)

    def test_request_id_malformed_replaced(self) -> None:
        """Verify unsafe or malformed correlation ID is discarded and replaced."""
        malformed_id = "bad id with spaces and <script>alert(1)</script>"
        response = self.client.get("/health/live", headers={"X-Request-ID": malformed_id})
        self.assertEqual(response.status_code, 200)
        propagated_id = response.headers.get("x-request-id")
        self.assertNotEqual(propagated_id, malformed_id)
        self.assertNotIn("script", propagated_id)

    def test_security_headers_present(self) -> None:
        """Verify defensive HTTP security headers are injected on all responses."""
        response = self.client.get("/info")
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(response.headers.get("x-frame-options"), "DENY")
        self.assertEqual(response.headers.get("x-xss-protection"), "1; mode=block")
        self.assertEqual(response.headers.get("referrer-policy"), "strict-origin-when-cross-origin")
        self.assertEqual(response.headers.get("x-dera-policy"), "DETERMINISTIC_ZERO_AI")

    def test_cors_allowed_origin(self) -> None:
        """Verify CORS preflight and access from an allowed origin."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
        response = self.client.options("/health/live", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:3000",
        )

    def test_cors_rejected_origin(self) -> None:
        """Verify CORS header is absent for untrusted origins."""
        response = self.client.get(
            "/health/live", headers={"Origin": "https://unauthorized-domain.com"}
        )
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_not_found_404_handling(self) -> None:
        """Verify requesting unknown route returns HTTP 404 with structured error response."""
        response = self.client.get("/nonexistent/endpoint")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], "HTTP_404")

    def test_method_not_allowed_405_handling(self) -> None:
        """Verify unsupported HTTP method returns HTTP 405 with structured error response."""
        response = self.client.post("/health/live")
        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], "HTTP_405")


if __name__ == "__main__":
    unittest.main()
