"""Unit & Adversarial Tests for Read-Only Query Enforcement.

Validates that all forms of DDL/DML, comment escapes, stacked queries, administrative
procedures, and unsafe PRAGMAs are strictly rejected while legitimate introspection queries pass.
"""

import unittest

from dera_connectors.security import (
    ReadOnlySecurityViolationError,
    strip_sql_comments_and_literals,
    validate_read_only_sql,
)


class TestReadOnlyEnforcement(unittest.TestCase):
    """Test suite verifying lexical analysis and read-only query invariants."""

    def test_legitimate_introspection_queries_pass(self) -> None:
        """Verify standard SELECT queries, catalog queries, and EXPLAIN queries pass."""
        safe_queries = [
            "SELECT table_name, table_schema FROM information_schema.tables WHERE table_schema = 'public'",
            "SELECT column_name, data_type, is_nullable FROM information_schema.columns ORDER BY ordinal_position",
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'orders'",
            "PRAGMA table_info('users')",
            "PRAGMA table_xinfo('audit_logs')",
            "PRAGMA foreign_key_list('orders')",
            "PRAGMA index_list('customers')",
            "PRAGMA index_xinfo('idx_customer_email')",
            "SHOW FULL TABLES WHERE Table_type != 'VIEW'",
            "DESCRIBE information_schema.columns",
            "EXPLAIN SELECT * FROM users WHERE active = true",
        ]
        for query in safe_queries:
            try:
                validate_read_only_sql(query)
            except ReadOnlySecurityViolationError:
                self.fail(f"Legitimate query was rejected: {query}")

    def test_query_with_mutation_keywords_inside_string_literals_passes(self) -> None:
        """Verify queries with keywords like 'drop', 'delete', 'create' inside string literals pass."""
        queries_with_literals = [
            "SELECT * FROM audit_events WHERE action = 'drop' AND status = 'completed'",
            "SELECT * FROM tasks WHERE command = 'CREATE TABLE test' AND user_id = 42",
            "SELECT * FROM logs WHERE message LIKE '%delete from orders%'",
            "SELECT * FROM settings WHERE config_key = 'truncate'",
        ]
        for query in queries_with_literals:
            try:
                validate_read_only_sql(query)
            except ReadOnlySecurityViolationError:
                self.fail(f"Query with keyword in string literal was falsely rejected: {query}")

    def test_all_ddl_and_dml_mutations_rejected(self) -> None:
        """Verify all standard DDL/DML mutation keywords are blocked."""
        mutations = [
            ("DROP TABLE users", "DROP"),
            ("TRUNCATE TABLE audit_log", "TRUNCATE"),
            ("ALTER TABLE accounts ADD COLUMN balance NUMERIC", "ALTER"),
            ("CREATE TABLE injected (id INT)", "CREATE"),
            ("INSERT INTO users VALUES (1, 'alice')", "INSERT"),
            ("UPDATE accounts SET balance = 0", "UPDATE"),
            ("DELETE FROM users WHERE id = 1", "DELETE"),
            ("GRANT ALL PRIVILEGES ON DATABASE prod TO mallory", "GRANT"),
            ("REVOKE SELECT ON users FROM reader", "REVOKE"),
            ("REPLACE INTO settings VALUES ('key', 'val')", "REPLACE"),
            ("EXECUTE sp_delete_customer", "EXECUTE"),
            ("EXEC sp_evil", "EXEC"),
            ("CALL purge_records()", "CALL"),
            ("MERGE INTO target USING source ON target.id = source.id", "MERGE"),
            ("VACUUM FULL", "VACUUM"),
            ("REINDEX TABLE users", "REINDEX"),
            ("LOCK TABLE users IN EXCLUSIVE MODE", "LOCK"),
            ("RENAME TABLE old_name TO new_name", "RENAME"),
            ("SHUTDOWN", "SHUTDOWN"),
            ("ATTACH DATABASE '/tmp/evil.db' AS evil", "ATTACH"),
            ("DETACH DATABASE evil", "DETACH"),
        ]
        for query, expected_token in mutations:
            with self.assertRaises(
                ReadOnlySecurityViolationError,
                msg=f"Mutation '{query}' was not blocked.",
            ) as ctx:
                validate_read_only_sql(query)
            self.assertIn(expected_token, ctx.exception.message)

    def test_comment_wrapped_mutations_rejected(self) -> None:
        """Verify attackers cannot hide mutations behind SQL comments."""
        comment_attempts = [
            "/* safe comment */ DROP TABLE users;",
            "/**/DROP TABLE users;",
            "-- line comment\nDROP TABLE users;",
            "# mysql line comment\nDROP TABLE users;",
            "SELECT 1; /* inline */ DROP TABLE users;",
            "SELECT * FROM users; --\nDELETE FROM users;",
        ]
        for query in comment_attempts:
            with self.assertRaises(
                ReadOnlySecurityViolationError,
                msg=f"Comment-wrapped query '{query}' was not blocked.",
            ):
                validate_read_only_sql(query)

    def test_dangerous_administrative_functions_rejected(self) -> None:
        """Verify dangerous PostgreSQL/SQLite/MySQL functions are blocked."""
        dangerous = [
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity",
            "SELECT pg_cancel_backend(1234)",
            "SELECT pg_read_file('/etc/passwd')",
            "SELECT pg_write_file('/tmp/pwn', 'data')",
            "SELECT load_extension('libevil.so')",
            "SELECT xp_cmdshell('whoami')",
            "SELECT sys_eval('id')",
        ]
        for query in dangerous:
            with self.assertRaises(
                ReadOnlySecurityViolationError,
                msg=f"Dangerous function query '{query}' was not blocked.",
            ):
                validate_read_only_sql(query)

    def test_file_io_escape_commands_rejected(self) -> None:
        """Verify INTO OUTFILE and COPY FROM are blocked."""
        file_io_queries = [
            "SELECT * FROM users INTO OUTFILE '/tmp/users.txt'",
            "SELECT * FROM users INTO DUMPFILE '/tmp/users.bin'",
            "COPY users FROM '/tmp/malicious.csv'",
        ]
        for query in file_io_queries:
            with self.assertRaises(
                ReadOnlySecurityViolationError,
                msg=f"File IO query '{query}' was not blocked.",
            ):
                validate_read_only_sql(query)

    def test_disallowed_sqlite_pragmas_rejected(self) -> None:
        """Verify mutating or dangerous SQLite PRAGMAs are rejected."""
        bad_pragmas = [
            "PRAGMA writable_schema = ON",
            "PRAGMA foreign_key_check",
            "PRAGMA integrity_check",
            "PRAGMA optimize",
            "PRAGMA shrink_memory",
        ]
        for pragma in bad_pragmas:
            with self.assertRaises(
                ReadOnlySecurityViolationError,
                msg=f"Disallowed PRAGMA '{pragma}' was not blocked.",
            ):
                validate_read_only_sql(pragma)

    def test_strip_sql_comments_and_literals(self) -> None:
        """Verify lexical helper strips comments and replaces literals."""
        raw = "SELECT 'drop table' FROM users -- comment here\nWHERE id = 1 /* block */"
        cleaned = strip_sql_comments_and_literals(raw)
        self.assertNotIn("comment here", cleaned)
        self.assertNotIn("block", cleaned)
        self.assertNotIn("drop table", cleaned)
        self.assertIn("SELECT", cleaned)
        self.assertIn("FROM users", cleaned)


if __name__ == "__main__":
    unittest.main()
