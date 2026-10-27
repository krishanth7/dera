"""Tests for OpenAPI breaking-change detection and backward compatibility (Phase 4.2)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Add repo root to import validate_openapi
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "scripts" / "ci"))

from validate_openapi import detect_breaking_changes  # noqa: E402


class TestApiCompatibility(unittest.TestCase):
    """Validate detect_breaking_changes correctly flags regressions and permits additive changes."""

    def test_identical_specs_have_no_breaking_changes(self) -> None:
        """Verify identical baseline and candidate return empty breaking changes."""
        spec = {
            "paths": {
                "/api/v1/health": {
                    "get": {
                        "parameters": [],
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            }
        }
        changes = detect_breaking_changes(spec, spec)
        self.assertEqual(changes, [])

    def test_removed_path_is_breaking(self) -> None:
        """Verify removing an existing endpoint path is flagged as breaking."""
        baseline = {
            "paths": {
                "/api/v1/health": {"get": {"responses": {"200": {}}}},
                "/api/v1/catalogs": {"get": {"responses": {"200": {}}}},
            }
        }
        candidate = {
            "paths": {
                "/api/v1/health": {"get": {"responses": {"200": {}}}},
            }
        }
        changes = detect_breaking_changes(baseline, candidate)
        self.assertTrue(
            any("Removed endpoint path" in c and "/api/v1/catalogs" in c for c in changes)
        )

    def test_removed_http_method_is_breaking(self) -> None:
        """Verify removing a method from an existing path is flagged as breaking."""
        baseline = {
            "paths": {
                "/api/v1/health": {
                    "get": {"responses": {"200": {}}},
                    "head": {"responses": {"200": {}}},
                }
            }
        }
        candidate = {
            "paths": {
                "/api/v1/health": {
                    "get": {"responses": {"200": {}}},
                }
            }
        }
        changes = detect_breaking_changes(baseline, candidate)
        self.assertTrue(any("HEAD" in c and "Removed HTTP method" in c for c in changes))

    def test_new_required_parameter_is_breaking(self) -> None:
        """Verify adding a newly required query/header/path parameter is flagged as breaking."""
        baseline = {
            "paths": {
                "/api/v1/items": {
                    "get": {
                        "parameters": [
                            {"name": "page", "in": "query", "required": False},
                        ],
                        "responses": {"200": {}},
                    }
                }
            }
        }
        candidate = {
            "paths": {
                "/api/v1/items": {
                    "get": {
                        "parameters": [
                            {"name": "page", "in": "query", "required": False},
                            {"name": "api_key", "in": "header", "required": True},
                        ],
                        "responses": {"200": {}},
                    }
                }
            }
        }
        changes = detect_breaking_changes(baseline, candidate)
        self.assertTrue(any("required parameter" in c and "api_key" in c for c in changes))

    def test_removed_success_status_code_is_breaking(self) -> None:
        """Verify removing an existing successful status code (200, 201) is flagged as breaking."""
        baseline = {
            "paths": {
                "/api/v1/items": {
                    "get": {
                        "responses": {
                            "200": {"description": "Standard list"},
                            "204": {"description": "Empty list"},
                        }
                    }
                }
            }
        }
        candidate = {
            "paths": {
                "/api/v1/items": {
                    "get": {
                        "responses": {
                            "200": {"description": "Standard list"},
                        }
                    }
                }
            }
        }
        changes = detect_breaking_changes(baseline, candidate)
        self.assertTrue(any("Removed success status code '204'" in c for c in changes))

    def test_additive_changes_are_allowed(self) -> None:
        """Verify adding new routes, optional parameters, and status codes does NOT flag breaking changes."""
        baseline = {
            "paths": {
                "/api/v1/health": {"get": {"responses": {"200": {}}}},
            }
        }
        candidate = {
            "paths": {
                "/api/v1/health": {
                    "get": {
                        "parameters": [
                            {"name": "verbose", "in": "query", "required": False},
                        ],
                        "responses": {"200": {}},
                    }
                },
                "/api/v1/new-feature": {
                    "get": {"responses": {"200": {}}},
                },
            }
        }
        changes = detect_breaking_changes(baseline, candidate)
        self.assertEqual(changes, [])
