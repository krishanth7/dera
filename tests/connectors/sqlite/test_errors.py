"""Unit tests for SQLite error taxonomy mapping and path sanitization."""

import sqlite3
import unittest

from dera_connectors.errors import (
    ConnectorMetadataError,
    ConnectorPermissionDeniedError,
    ConnectorSecurityViolationError,
    ConnectorTimeoutError,
    ConnectorUnavailableError,
)
from dera_connectors.sqlite.errors import map_sqlite_error, sanitize_sqlite_error_message


class TestSqliteErrorMapping(unittest.TestCase):
    """Test suite for SQLite exception classification and path masking."""

    def test_sanitize_sqlite_error_message_linux(self) -> None:
        """Verify that POSIX filesystem paths are sanitized."""
        msg = "unable to open database file: /var/secrets/workspace_42/app.db"
        sanitized = sanitize_sqlite_error_message(msg)
        self.assertNotIn("/var/secrets", sanitized)
        self.assertIn("[REDACTED_PATH]", sanitized)

    def test_sanitize_sqlite_error_message_windows(self) -> None:
        """Verify that Windows filesystem paths are sanitized."""
        msg = "disk I/O error on C:\\Users\\Admin\\AppData\\db.sqlite"
        sanitized = sanitize_sqlite_error_message(msg)
        self.assertNotIn("Users\\Admin", sanitized)
        self.assertIn("[REDACTED_PATH]", sanitized)

    def test_map_readonly_violation(self) -> None:
        """Verify mapping of attempt to write a readonly database."""
        exc = sqlite3.OperationalError("attempt to write a readonly database")
        err = map_sqlite_error(exc, database="app.db")
        self.assertIsInstance(err, ConnectorSecurityViolationError)

    def test_map_permission_denied(self) -> None:
        """Verify mapping of permission denied errors."""
        exc = PermissionError("Permission denied: /opt/dera/data.db")
        err = map_sqlite_error(exc, database="data.db")
        self.assertIsInstance(err, ConnectorPermissionDeniedError)

    def test_map_database_locked(self) -> None:
        """Verify mapping of database locked / busy timeout."""
        exc = sqlite3.OperationalError("database is locked")
        err = map_sqlite_error(exc, database="data.db")
        self.assertIsInstance(err, ConnectorTimeoutError)

    def test_map_unavailable_database(self) -> None:
        """Verify mapping of unable to open database file."""
        exc = sqlite3.OperationalError("unable to open database file")
        err = map_sqlite_error(exc, database="data.db")
        self.assertIsInstance(err, ConnectorUnavailableError)

    def test_map_corrupt_database(self) -> None:
        """Verify mapping of malformed disk image / not a database."""
        exc = sqlite3.DatabaseError("file is not a database")
        err = map_sqlite_error(exc, database="corrupt.db")
        self.assertIsInstance(err, ConnectorMetadataError)
