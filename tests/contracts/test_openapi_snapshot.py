"""Tests for OpenAPI snapshot consistency and zero-drift verification (Phase 4.2)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from dera_api.factory import create_app

ROOT_DIR = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = ROOT_DIR / "docs" / "api" / "openapi.v1.json"


class TestOpenAPISnapshot(unittest.TestCase):
    """Validate that the active FastAPI OpenAPI schema exactly matches docs/api/openapi.v1.json."""

    def test_openapi_snapshot_file_exists(self) -> None:
        """Verify the canonical OpenAPI artifact exists on disk."""
        self.assertTrue(
            SNAPSHOT_PATH.is_file(), f"Missing OpenAPI snapshot file at {SNAPSHOT_PATH}"
        )

    def test_openapi_live_matches_snapshot(self) -> None:
        """Verify live application openapi schema has zero drift against committed snapshot."""
        app = create_app()
        live_schema = app.openapi()

        with open(SNAPSHOT_PATH, encoding="utf-8") as f:
            snapshot_schema = json.load(f)

        self.assertEqual(
            live_schema,
            snapshot_schema,
            "Live OpenAPI schema differs from docs/api/openapi.v1.json! "
            "Run 'python scripts/ci/validate_openapi.py --update' to regenerate the snapshot if changes are intentional.",
        )

    def test_openapi_version_and_metadata(self) -> None:
        """Verify OpenAPI 3.1.x standard and core metadata."""
        app = create_app()
        schema = app.openapi()

        self.assertTrue(schema.get("openapi", "").startswith("3.1."))
        info = schema.get("info", {})
        self.assertEqual(info.get("title"), "DERA API Gateway")
        self.assertEqual(info.get("version"), "0.1.0-dev")

    def test_all_routes_have_operation_ids(self) -> None:
        """Verify every defined operation has a non-empty, unique operationId."""
        app = create_app()
        schema = app.openapi()
        paths = schema.get("paths", {})

        operation_ids: set[str] = set()
        for path_url, path_item in paths.items():
            for method, operation in path_item.items():
                if method in {"get", "post", "put", "delete", "patch", "options", "head"}:
                    op_id = operation.get("operationId")
                    self.assertTrue(op_id, f"Missing operationId for {method.upper()} {path_url}")
                    self.assertNotIn(
                        op_id,
                        operation_ids,
                        f"Duplicate operationId '{op_id}' in {method.upper()} {path_url}",
                    )
                    operation_ids.add(op_id)
