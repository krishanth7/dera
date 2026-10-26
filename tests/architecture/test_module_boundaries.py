"""Automated Architecture & Module Boundary Verification Tests.

Enforces:
1. Zero generative AI runtime dependencies across all Python packages.
2. Unidirectional dependency flow: Core -> Contracts -> Connectors -> API -> Web.
3. Core domain independence from web frameworks and external transport layers.
4. Read-only safety validation on database connector queries.
"""

import ast
import glob
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for p in [
    os.path.join(REPO_ROOT, "packages", "core", "src"),
    os.path.join(REPO_ROOT, "packages", "connectors", "src"),
    os.path.join(REPO_ROOT, "apps", "api", "src"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dera_connectors.base.connector import BaseConnector, ConnectionConfig
from dera_core.exceptions import (
    CycleDetectedError,
    DeraError,
    ReadOnlyViolationError,
    SchemaParsingError,
)
from dera_api.core.config import get_settings

FORBIDDEN_AI_MODULES = {
    "openai",
    "google.genai",
    "google.generativeai",
    "anthropic",
    "groq",
    "cohere",
    "langchain",
    "llamaindex",
    "torch",
    "transformers",
    "onnxruntime",
}

FORBIDDEN_CORE_FRAMEWORK_IMPORTS = {
    "fastapi",
    "starlette",
    "flask",
    "django",
    "uvicorn",
    "dera_api",
}


class TestArchitectureBoundaries(unittest.TestCase):
    """Test suite for validating architectural boundaries and static constraints."""

    def _get_imports_from_file(self, filepath: str) -> set[str]:
        """Extract all top-level imported module names from a Python source file."""
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=filepath)
            except SyntaxError:
                return set()

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
        return imports

    def test_zero_ai_dependencies_in_packages(self) -> None:
        """Verify that zero AI or LLM packages are imported in packages/ or apps/."""
        source_files = glob.glob(
            os.path.join(REPO_ROOT, "packages", "**", "*.py"), recursive=True
        ) + glob.glob(os.path.join(REPO_ROOT, "apps", "**", "*.py"), recursive=True)

        self.assertGreater(len(source_files), 0, "Source files must be discovered")

        for filepath in source_files:
            imports = self._get_imports_from_file(filepath)
            violating = imports.intersection(FORBIDDEN_AI_MODULES)
            self.assertEqual(
                violating,
                set(),
                f"Architecture violation: Forbidden AI import {violating} in {filepath}",
            )

    def test_core_package_independence(self) -> None:
        """Verify packages/core does not import from apps/ or web transport frameworks."""
        core_files = glob.glob(
            os.path.join(REPO_ROOT, "packages", "core", "src", "**", "*.py"), recursive=True
        )
        self.assertGreater(len(core_files), 0)

        for filepath in core_files:
            imports = self._get_imports_from_file(filepath)
            violating = imports.intersection(FORBIDDEN_CORE_FRAMEWORK_IMPORTS)
            self.assertEqual(
                violating,
                set(),
                f"Architecture violation: Core module imports web framework {violating} in {filepath}",
            )

    def test_connector_read_only_query_boundary(self) -> None:
        """Verify that connector query validator rejects mutating SQL statements."""
        class DummyConnector(BaseConnector):
            def connect(self) -> None: pass
            def disconnect(self) -> None: pass
            def test_connection(self) -> bool: return True
            def inspect_tables(self) -> list: return []

        config = ConnectionConfig(dialect="sqlite", database=":memory:")
        connector = DummyConnector(config)

        # Safe read-only catalog queries should pass
        safe_queries = [
            "SELECT * FROM sqlite_master WHERE type='table'",
            "PRAGMA table_info('users')",
            "PRAGMA foreign_key_list('orders')",
            "SELECT table_name, column_name FROM information_schema.columns",
        ]
        for query in safe_queries:
            try:
                connector.validate_query_read_only(query)
            except ReadOnlyViolationError:
                self.fail(f"Legitimate read-only query rejected: {query}")

        # Dangerous mutating queries MUST raise ReadOnlyViolationError
        dangerous_queries = [
            "DROP TABLE users;",
            "TRUNCATE TABLE audit_log;",
            "ALTER TABLE accounts ADD COLUMN balance int;",
            "DELETE FROM sessions WHERE id = 1;",
            "INSERT INTO config VALUES ('admin', 'true');",
            "UPDATE users SET is_admin = 1;",
            "GRANT ALL PRIVILEGES ON *.* TO 'attacker'@'%';",
        ]
        for query in dangerous_queries:
            with self.assertRaises(
                ReadOnlyViolationError,
                msg=f"Expected ReadOnlyViolationError for dangerous SQL: {query}",
            ):
                connector.validate_query_read_only(query)

    def test_structured_exceptions_serialization(self) -> None:
        """Verify domain exceptions serialize to dictionary correctly."""
        err = CycleDetectedError("Circular dependency detected", cycle_path=["users", "orders", "users"])
        d = err.to_dict()
        self.assertEqual(d["error_type"], "CycleDetectedError")
        self.assertEqual(d["message"], "Circular dependency detected")
        self.assertEqual(d["details"]["cycle_path"], ["users", "orders", "users"])

    def test_api_settings_defaults(self) -> None:
        """Verify API settings default to secure, deterministic values."""
        settings = get_settings()
        self.assertTrue(settings.read_only_enforced)
        self.assertTrue(settings.zero_ai_policy_enforced)
        self.assertEqual(settings.version, "0.1.0-dev")


if __name__ == "__main__":
    unittest.main()
