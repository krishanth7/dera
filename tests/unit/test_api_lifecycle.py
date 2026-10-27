"""Unit tests for DERA API lifespan management and readiness state.

Validates startup initialization, graceful shutdown state transitions,
and truthful readiness reporting.
"""

import unittest

from dera_api.core.lifespan import get_application_readiness
from dera_api.factory import create_app
from fastapi.testclient import TestClient


class TestApiLifecycle(unittest.TestCase):
    """Test suite for validating application lifecycle and readiness state."""

    def test_lifespan_state_transitions(self) -> None:
        """Verify startup and shutdown transitions using TestClient context."""
        app = create_app()

        # Before startup context
        initial_readiness = get_application_readiness(app)
        self.assertFalse(initial_readiness["ready"])

        with TestClient(app) as client:
            # Active context: app should be initialized and ready
            active_readiness = get_application_readiness(app)
            self.assertTrue(active_readiness["ready"])
            self.assertIsNotNone(active_readiness["startup_time"])
            self.assertEqual(
                active_readiness["subsystems"]["application_state"],
                "operational",
            )

            # Health readiness endpoint should return 200 OK
            response = client.get("/health/ready")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "ok")
            self.assertTrue(data["ready"])
            self.assertEqual(
                data["subsystems"]["database_connectors"],
                "none_required_in_phase_4_1",
            )

        # After shutdown context
        post_shutdown_readiness = get_application_readiness(app)
        self.assertFalse(post_shutdown_readiness["ready"])

    def test_readiness_probe_when_unready(self) -> None:
        """Verify /health/ready returns HTTP 503 when app.state.is_ready is False."""
        app = create_app()

        with TestClient(app) as client:
            # Manually simulate unready state
            app.state.is_ready = False

            response = client.get("/health/ready")
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertEqual(data["status"], "not_ready")
            self.assertFalse(data["ready"])


if __name__ == "__main__":
    unittest.main()
