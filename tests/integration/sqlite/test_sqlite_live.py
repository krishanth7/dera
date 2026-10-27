"""Live SQLite integration, WAL-mode, and read-only security test suite.

Verifies end-to-end introspection against real SQLite 3 database files,
including complex schemas (STRICT, WITHOUT ROWID, generated columns, composite keys,
partial/expression indexes, unicode/mixed-case identifiers, triggers, views),
WAL-mode operation, and strict read-only security defense-in-depth.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import tempfile
import unittest

from dera_connectors.capabilities import ConnectorCapability
from dera_connectors.engine import DatabaseEngine
from dera_connectors.errors import (
    ConnectorError,
    ConnectorSecurityViolationError,
    ConnectorUnavailableError,
)
from dera_connectors.sqlite.adapter import SqliteConnector
from dera_connectors.sqlite.configuration import SqliteConnectorConfig


class TestSqliteLiveIntegration(unittest.IsolatedAsyncioTestCase):
    """End-to-end integration and security test suite against real SQLite databases."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create disposable SQLite fixtures including WAL database, corrupt file, and target DB."""
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.approved_root = cls.temp_dir.name

        cls.db_path = os.path.join(cls.approved_root, "live_production.db")
        cls.wal_db_path = os.path.join(cls.approved_root, "wal_database.db")
        cls.corrupt_db_path = os.path.join(cls.approved_root, "corrupted.db")

        # 1. Initialize main test database
        conn = sqlite3.connect(cls.db_path)
        cur = conn.cursor()
        cur.executescript(
            """
            -- 1. Departments table
            CREATE TABLE departments (
                dept_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL
            );

            -- 2. Employees table with generated column, composite check, and FK
            CREATE TABLE employees (
                emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
                dept_id INTEGER NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                full_name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
                salary REAL NOT NULL,
                status TEXT DEFAULT 'active' NOT NULL,
                CONSTRAINT chk_emp_salary CHECK (salary > 0.0),
                CONSTRAINT chk_emp_status CHECK (status IN ('active', 'suspended', 'terminated')),
                FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
                    ON UPDATE CASCADE ON DELETE RESTRICT
            );

            -- 3. Partial index on active employees
            CREATE INDEX idx_emp_active ON employees(dept_id) WHERE status = 'active';

            -- 4. Expression index on lower(code)
            CREATE INDEX idx_dept_lower_code ON departments(lower(code));

            -- 5. Composite primary key table
            CREATE TABLE project_assignments (
                project_id INTEGER NOT NULL,
                emp_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                assigned_date TEXT NOT NULL,
                PRIMARY KEY (project_id, emp_id),
                FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
            );

            -- 6. STRICT table
            CREATE TABLE config_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL,
                is_active INTEGER NOT NULL
            ) STRICT;

            -- 7. WITHOUT ROWID table
            CREATE TABLE session_cache (
                session_token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at INTEGER NOT NULL
            ) WITHOUT ROWID;

            -- 8. Unicode and mixed-case identifier table
            CREATE TABLE "Special_Café_Data" (
                "Item_ID" INTEGER PRIMARY KEY,
                "Prod_Name" TEXT NOT NULL,
                "Price_€" REAL NOT NULL
            );

            -- 9. Analytical View
            CREATE VIEW v_dept_headcount AS
            SELECT d.name AS dept_name, count(e.emp_id) AS total_employees
            FROM departments d LEFT JOIN employees e ON d.dept_id = e.dept_id
            GROUP BY d.dept_id, d.name;

            -- 10. Trigger
            CREATE TRIGGER trg_audit_emp_delete
            AFTER DELETE ON employees
            BEGIN
                SELECT 1;
            END;

            -- Seed minimal fixture rows
            INSERT INTO departments (dept_id, name, code) VALUES (1, 'Engineering', 'ENG');
            INSERT INTO departments (dept_id, name, code) VALUES (2, 'Finance', 'FIN');
            INSERT INTO employees (dept_id, first_name, last_name, salary, status)
                VALUES (1, 'Alan', 'Turing', 120000.0, 'active');
            INSERT INTO employees (dept_id, first_name, last_name, salary, status)
                VALUES (2, 'Ada', 'Lovelace', 130000.0, 'active');
            INSERT INTO config_settings (setting_key, setting_value, is_active)
                VALUES ('site_maintenance', 'false', 0);
            INSERT INTO session_cache (session_token, user_id, expires_at)
                VALUES ('tok_abc123', 1, 1893456000);
            INSERT INTO "Special_Café_Data" ("Item_ID", "Prod_Name", "Price_€")
                VALUES (101, 'Espresso', 2.50);
            """
        )
        conn.commit()
        conn.close()

        # Record hash of database file to verify immutability
        with open(cls.db_path, "rb") as f:
            cls.initial_db_hash = hashlib.sha256(f.read()).hexdigest()

        # 2. Initialize WAL mode database
        wal_conn = sqlite3.connect(cls.wal_db_path)
        wal_conn.execute("PRAGMA journal_mode = WAL;")
        wal_conn.execute("CREATE TABLE wal_entries (id INT PRIMARY KEY, msg TEXT);")
        wal_conn.execute("INSERT INTO wal_entries VALUES (1, 'written in wal mode');")
        wal_conn.commit()
        wal_conn.close()

        # 3. Create corrupt database file (invalid header)
        with open(cls.corrupt_db_path, "wb") as f:
            f.write(b"NOT A SQLITE DATABASE FILE HEADER RANDOM BYTES 0123456789")

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up disposable test resources."""
        try:
            cls.temp_dir.cleanup()
        except Exception:
            pass

    def _get_connector(
        self,
        db_path: str,
        immutable: bool = False,
    ) -> SqliteConnector:
        """Factory helper creating configured SqliteConnector bound to approved root."""
        config = SqliteConnectorConfig(
            database=db_path,
            approved_storage_roots=[self.approved_root],
            immutable_snapshot=immutable,
            allow_memory_databases=False,
        )
        return SqliteConnector(config)

    async def test_live_connection_identity(self) -> None:
        """Verify connection establishment and SQLite runtime identity discovery."""
        async with self._get_connector(self.db_path) as conn:
            identity = await conn.get_identity()
            self.assertEqual(identity.engine, DatabaseEngine.SQLITE)
            self.assertIn("3.", identity.server_version)
            self.assertIn("c_version", identity.server_capability_hints)

    async def test_live_capabilities_discovery(self) -> None:
        """Verify discovery of supported and unsupported SQLite capabilities."""
        async with self._get_connector(self.db_path) as conn:
            caps = await conn.get_capabilities()
            self.assertEqual(caps.engine, DatabaseEngine.SQLITE)
            # Supported
            self.assertTrue(caps.is_supported(ConnectorCapability.TABLE_ENUMERATION))
            self.assertTrue(caps.is_supported(ConnectorCapability.COLUMN_INSPECTION))
            self.assertTrue(caps.is_supported(ConnectorCapability.PRIMARY_KEY_INSPECTION))
            self.assertTrue(caps.is_supported(ConnectorCapability.FOREIGN_KEY_INSPECTION))
            self.assertTrue(caps.is_supported(ConnectorCapability.UNIQUE_CONSTRAINT_INSPECTION))
            self.assertTrue(caps.is_supported(ConnectorCapability.CHECK_CONSTRAINT_INSPECTION))
            self.assertTrue(caps.is_supported(ConnectorCapability.INDEX_INSPECTION))
            self.assertTrue(caps.is_supported(ConnectorCapability.VIEW_INSPECTION))
            self.assertTrue(caps.is_supported(ConnectorCapability.TRIGGER_INSPECTION))
            # Unsupported (Postgres/Network-only)
            self.assertFalse(caps.is_supported(ConnectorCapability.MATERIALIZED_VIEW_INSPECTION))
            self.assertFalse(caps.is_supported(ConnectorCapability.PROCEDURE_INSPECTION))
            self.assertFalse(caps.is_supported(ConnectorCapability.SEQUENCE_INSPECTION))

    async def test_live_table_enumeration(self) -> None:
        """Verify deterministic table enumeration, STRICT, and WITHOUT ROWID detection."""
        async with self._get_connector(self.db_path) as conn:
            tables = await conn.list_tables("main")
            table_map = {t.table_name: t for t in tables}

            # All user tables discovered
            expected = {
                "departments",
                "employees",
                "project_assignments",
                "config_settings",
                "session_cache",
                "Special_Café_Data",
            }
            self.assertTrue(expected.issubset(set(table_map.keys())))

            # Verify STRICT table detected
            self.assertTrue(table_map["config_settings"].engine_specific.get("is_strict"))

            # Verify WITHOUT ROWID table detected
            self.assertTrue(table_map["session_cache"].engine_specific.get("without_rowid"))

    async def test_live_column_and_generated_column_inspection(self) -> None:
        """Verify column types, nullability, defaults, and generated column flags."""
        async with self._get_connector(self.db_path) as conn:
            cols = await conn.list_columns("main", "employees")
            col_map = {c.column_name: c for c in cols}

            # Normal column
            self.assertIn("first_name", col_map)
            self.assertEqual(col_map["first_name"].data_type, "TEXT")
            self.assertFalse(col_map["first_name"].is_nullable)

            # Generated column
            self.assertIn("full_name", col_map)
            self.assertTrue(col_map["full_name"].is_generated)

            # Default value
            self.assertIn("status", col_map)
            self.assertIn("'active'", col_map["status"].default_expression or "")

    async def test_live_composite_primary_key(self) -> None:
        """Verify composite primary key discovery on project_assignments."""
        async with self._get_connector(self.db_path) as conn:
            pk = await conn.get_primary_key("main", "project_assignments")
            self.assertIsNotNone(pk)
            assert pk is not None
            self.assertEqual(pk.table_name, "project_assignments")
            self.assertEqual(pk.column_names, ["project_id", "emp_id"])

    async def test_live_foreign_key_inspection(self) -> None:
        """Verify foreign key mapping and actions on employees table."""
        async with self._get_connector(self.db_path) as conn:
            fks = await conn.list_foreign_keys("main", "employees")
            self.assertEqual(len(fks), 1)
            fk = fks[0]
            self.assertEqual(fk.table_name, "employees")
            self.assertEqual(fk.column_names, ["dept_id"])
            self.assertEqual(fk.referenced_table, "departments")
            self.assertEqual(fk.referenced_columns, ["dept_id"])
            self.assertEqual(fk.on_update, "CASCADE")
            self.assertEqual(fk.on_delete, "RESTRICT")

    async def test_live_check_constraints(self) -> None:
        """Verify check constraint extraction from DDL."""
        async with self._get_connector(self.db_path) as conn:
            checks = await conn.list_check_constraints("main", "employees")
            clauses = [c.check_clause for c in checks]
            self.assertTrue(any("salary > 0.0" in cl for cl in clauses))
            self.assertTrue(any("status IN" in cl for cl in clauses))

    async def test_live_partial_and_expression_indexes(self) -> None:
        """Verify partial and expression index detection."""
        async with self._get_connector(self.db_path) as conn:
            # Partial index
            emp_idxs = await conn.list_indexes("main", "employees")
            partial_idx = next((i for i in emp_idxs if i.index_name == "idx_emp_active"), None)
            self.assertIsNotNone(partial_idx)
            assert partial_idx is not None
            self.assertIsNotNone(partial_idx.predicate)
            self.assertTrue(partial_idx.engine_specific.get("is_partial"))

            # Expression index
            dept_idxs = await conn.list_indexes("main", "departments")
            expr_idx = next((i for i in dept_idxs if i.index_name == "idx_dept_lower_code"), None)
            self.assertIsNotNone(expr_idx)
            assert expr_idx is not None
            self.assertGreaterEqual(len(expr_idx.column_names), 1)

    async def test_live_views_and_triggers(self) -> None:
        """Verify views and triggers discovery without execution."""
        async with self._get_connector(self.db_path) as conn:
            views = await conn.list_views("main")
            self.assertTrue(any(v.view_name == "v_dept_headcount" for v in views))

            triggers = await conn.list_triggers("employees", "main")
            self.assertTrue(any(t.trigger_name == "trg_audit_emp_delete" for t in triggers))

    async def test_live_wal_mode_database_access(self) -> None:
        """Verify connector can read databases configured with WAL journal mode."""
        async with self._get_connector(self.wal_db_path) as conn:
            tables = await conn.list_tables("main")
            self.assertTrue(any(t.table_name == "wal_entries" for t in tables))
            cols = await conn.list_columns("main", "wal_entries")
            self.assertEqual(len(cols), 2)

    async def test_read_only_mutation_prevention(self) -> None:
        """Layer 3/4 Read-Only Defense in Depth: Verify any mutation attempt fails."""
        async with self._get_connector(self.db_path) as conn:
            mgr = conn._conn_mgr

            # 1. Attempt INSERT
            with self.assertRaises(Exception) as ctx:
                await mgr.execute_query("INSERT INTO departments VALUES (999, 'Hacked', 'HCK');")
            self.assertIn("readonly", str(ctx.exception).lower())

            # 2. Attempt UPDATE
            with self.assertRaises(Exception) as ctx:
                await mgr.execute_query(
                    "UPDATE departments SET name = 'Modified' WHERE dept_id = 1;"
                )
            self.assertIn("readonly", str(ctx.exception).lower())

            # 3. Attempt DELETE
            with self.assertRaises(Exception) as ctx:
                await mgr.execute_query("DELETE FROM departments WHERE dept_id = 1;")
            self.assertIn("readonly", str(ctx.exception).lower())

            # 4. Attempt CREATE TABLE
            with self.assertRaises(Exception) as ctx:
                await mgr.execute_query("CREATE TABLE malicious (id INT);")
            self.assertIn("readonly", str(ctx.exception).lower())

            # 5. Attempt DROP TABLE
            with self.assertRaises(Exception) as ctx:
                await mgr.execute_query("DROP TABLE departments;")
            self.assertIn("readonly", str(ctx.exception).lower())

    async def test_source_database_content_unmodified(self) -> None:
        """Verify that after extensive introspection, the source file bytes remain identical."""
        with open(self.db_path, "rb") as f:
            post_hash = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(self.initial_db_hash, post_hash, "Database file was altered!")

    async def test_filesystem_security_guards(self) -> None:
        """Verify directory traversal and unauthorized path rejection."""
        # 1. Path traversal outside approved root
        traversal_path = os.path.join(self.approved_root, "..", "secret.db")
        conn_traversal = self._get_connector(traversal_path)
        with self.assertRaises(ConnectorSecurityViolationError):
            await conn_traversal.connect()

        # 2. Non-existent database
        missing_path = os.path.join(self.approved_root, "does_not_exist.db")
        conn_missing = self._get_connector(missing_path)
        with self.assertRaises(ConnectorUnavailableError):
            await conn_missing.connect()

        # 3. Corrupted database header
        conn_corrupt = self._get_connector(self.corrupt_db_path)
        try:
            with self.assertRaises((ConnectorError, sqlite3.Error)):
                await conn_corrupt.connect()
                await conn_corrupt.list_tables()
        finally:
            await conn_corrupt.close()
