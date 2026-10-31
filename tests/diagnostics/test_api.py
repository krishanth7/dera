"""Tests for Phase 8.1 schema diagnostic REST API endpoints."""

from __future__ import annotations

import unittest

from dera_api.main import app
from fastapi.testclient import TestClient


class TestDiagnosticApi(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_list_diagnostic_rules(self) -> None:
        """Verifies GET /api/v1/reverse-engineering/diagnostics/rules returns registered rules."""
        response = self.client.get("/api/v1/reverse-engineering/diagnostics/rules")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        rule_ids = [r["rule_id"] for r in data]
        assert "DERA-SCHEMA-001" in rule_ids
        assert "DERA-SCHEMA-002" in rule_ids
        assert "DERA-SCHEMA-003" in rule_ids
        assert "DERA-SCHEMA-004" in rule_ids
        assert "DERA-SCHEMA-005" in rule_ids

    def test_get_diagnostic_rule_by_id(self) -> None:
        """Verifies GET /api/v1/reverse-engineering/diagnostics/rules/{rule_id}."""
        response = self.client.get("/api/v1/reverse-engineering/diagnostics/rules/DERA-SCHEMA-001")
        assert response.status_code == 200
        data = response.json()
        assert data["rule_id"] == "DERA-SCHEMA-001"
        assert data["title"] == "Unresolved Canonical Relationship Target"
        assert data["default_severity"] == "HIGH"
        assert data["category"] == "RELATIONSHIPS"

    def test_get_diagnostic_rule_not_found(self) -> None:
        """Verifies 404 response on unknown rule ID."""
        response = self.client.get("/api/v1/reverse-engineering/diagnostics/rules/DERA-UNKNOWN-999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
