"""Unit tests for DERA FastAPI gateway.

Deterministic endpoint validation.
Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

import unittest

try:
    from fastapi.testclient import TestClient
    from dera_api.main import app
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@unittest.skipUnless(FASTAPI_AVAILABLE, "FastAPI is not installed in the environment")
class TestDeraApi(unittest.TestCase):
    def setUp(self) -> None:
        if FASTAPI_AVAILABLE:
            self.client = TestClient(app)

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "dera-api")

    def test_info_endpoint(self) -> None:
        response = self.client.get("/info")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["project"], "DERA")
        self.assertEqual(data["maintainer"], "Krishanth")
        self.assertIn("Deterministic", data["philosophy"])


if __name__ == "__main__":
    unittest.main()
