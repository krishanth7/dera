"""Unit tests for SQLite filesystem isolation, traversal defense, and URI safety."""

import os
import tempfile
import unittest

from dera_connectors.errors import (
    ConnectorInvalidConfigurationError,
    ConnectorSecurityViolationError,
    ConnectorUnavailableError,
)
from dera_connectors.sqlite.filesystem import build_sqlite_readonly_uri, validate_sqlite_path


class TestSqliteFilesystemSecurity(unittest.TestCase):
    """Test suite for filesystem path validation and isolation rules."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.approved_root = os.path.realpath(self.temp_dir.name)
        # Create a disposable test sqlite file
        self.db_path = os.path.join(self.approved_root, "allowed.sqlite")
        with open(self.db_path, "wb") as f:
            f.write(b"")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_valid_path_within_approved_root(self) -> None:
        """Verify that file within approved root passes validation."""
        validated = validate_sqlite_path(
            self.db_path,
            approved_roots=[self.approved_root],
        )
        self.assertEqual(validated, self.db_path)

    def test_rejection_of_null_bytes(self) -> None:
        """Verify rejection of paths containing null byte injection."""
        with self.assertRaises(ConnectorInvalidConfigurationError):
            validate_sqlite_path(
                f"{self.db_path}\0evil.txt",
                approved_roots=[self.approved_root],
            )

    def test_rejection_of_prohibited_devices(self) -> None:
        """Verify rejection of special device paths (/dev/null, COM1, etc.)."""
        for dev in ("/dev/null", "\\\\.\\COM1", "CON.sqlite", "NUL.db"):
            with self.assertRaises(ConnectorSecurityViolationError):
                validate_sqlite_path(dev, approved_roots=[self.approved_root])

    def test_rejection_of_directory_traversal(self) -> None:
        """Verify that traversal (../) escaping approved root is rejected."""
        outside_path = os.path.join(self.approved_root, "..", "outside.sqlite")
        with self.assertRaises(ConnectorSecurityViolationError):
            validate_sqlite_path(
                outside_path,
                approved_roots=[self.approved_root],
            )

    def test_rejection_of_nonexistent_file(self) -> None:
        """Verify ConnectorUnavailableError for missing database files."""
        missing = os.path.join(self.approved_root, "missing.sqlite")
        with self.assertRaises(ConnectorUnavailableError):
            validate_sqlite_path(
                missing,
                approved_roots=[self.approved_root],
            )

    def test_rejection_of_directory_target(self) -> None:
        """Verify ConnectorInvalidConfigurationError when pointing to a directory."""
        with self.assertRaises(ConnectorInvalidConfigurationError):
            validate_sqlite_path(
                self.approved_root,
                approved_roots=[self.approved_root],
            )

    def test_build_sqlite_readonly_uri(self) -> None:
        """Verify deterministic build of SQLite read-only URI."""
        uri = build_sqlite_readonly_uri(self.db_path, immutable=False)
        self.assertTrue(uri.startswith("file:///"))
        self.assertIn("mode=ro", uri)
        self.assertNotIn("immutable=1", uri)

        immutable_uri = build_sqlite_readonly_uri(self.db_path, immutable=True)
        self.assertIn("mode=ro", immutable_uri)
        self.assertIn("immutable=1", immutable_uri)
