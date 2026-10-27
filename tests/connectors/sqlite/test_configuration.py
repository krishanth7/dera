"""Unit tests for SQLite connection configuration and root containment rules."""

import os
import unittest

from dera_connectors.engine import DatabaseEngine
from dera_connectors.sqlite.configuration import SqliteConnectorConfig


class TestSqliteConfiguration(unittest.TestCase):
    """Test suite for SqliteConnectorConfig invariants and constraints."""

    def test_valid_sqlite_configuration(self) -> None:
        """Verify normal configuration initialization with approved roots."""
        cwd = os.getcwd()
        config = SqliteConnectorConfig(
            database="test.sqlite",
            approved_storage_roots=[cwd],
            busy_timeout_ms=3000,
            immutable_snapshot=False,
        )
        self.assertEqual(config.engine, DatabaseEngine.SQLITE)
        self.assertEqual(config.database, "test.sqlite")
        self.assertEqual(config.busy_timeout_ms, 3000)
        self.assertFalse(config.immutable_snapshot)
        self.assertIn(os.path.realpath(cwd), config.approved_storage_roots)

    def test_rejection_of_network_host(self) -> None:
        """Verify that network host parameter is strictly rejected."""
        with self.assertRaises(ValueError) as ctx:
            SqliteConnectorConfig(
                database="test.sqlite",
                host="192.168.1.1",
            )
        self.assertIn("host", str(ctx.exception))

    def test_rejection_of_network_port(self) -> None:
        """Verify that network port parameter is strictly rejected."""
        with self.assertRaises(ValueError) as ctx:
            SqliteConnectorConfig(
                database="test.sqlite",
                port=5432,
            )
        self.assertIn("port", str(ctx.exception))

    def test_in_memory_prohibited_by_default(self) -> None:
        """Verify that in-memory database (:memory:) is rejected by default."""
        with self.assertRaises(ValueError) as ctx:
            SqliteConnectorConfig(database=":memory:")
        self.assertIn("allow_memory_databases", str(ctx.exception))

    def test_in_memory_allowed_when_flag_enabled(self) -> None:
        """Verify that in-memory database is permitted when allow_memory_databases=True."""
        config = SqliteConnectorConfig(
            database=":memory:",
            allow_memory_databases=True,
        )
        self.assertEqual(config.database, ":memory:")
        self.assertTrue(config.allow_memory_databases)
