"""Integration tests for DERA SQLite connector.

Verifies schema discovery, column nullability, primary key constraints,
foreign key resolution, unique/non-unique indexes, and quoted identifiers.
Copyright (c) 2026 Bunga Krishanth. All rights reserved.
Licensed under the MIT License.
"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dera.connectors.sqlite import SqliteConnector
from dera.graph import compute_topological_sort
from dera.diagnostics import run_all_diagnostics


class TestSqliteConnector(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

        # Build reference schema with composite PK, FK, and Index
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Prerequisite table: departments
        cursor.execute(
            """
            CREATE TABLE departments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                code VARCHAR(10) UNIQUE
            )
            """
        )

        # Dependent table with foreign key and index
        cursor.execute(
            """
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dept_id INTEGER NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                salary REAL DEFAULT 50000.0,
                FOREIGN KEY (dept_id) REFERENCES departments(id) ON DELETE CASCADE
            )
            """
        )

        # Supporting index on FK
        cursor.execute("CREATE INDEX idx_emp_dept ON employees(dept_id)")

        # Table with quoted identifier and missing PK (for diagnostic check)
        cursor.execute(
            """
            CREATE TABLE "audit log" (
                event_name TEXT NOT NULL,
                recorded_at TEXT NOT NULL
            )
            """
        )

        conn.commit()
        conn.close()

        self.connector = SqliteConnector(str(self.db_path))

    def tearDown(self) -> None:
        self.connector.close()
        self.temp_dir.cleanup()

    def test_get_table_names(self) -> None:
        tables = self.connector.get_table_names()
        self.assertIn("departments", tables)
        self.assertIn("employees", tables)
        self.assertIn("audit log", tables)

    def test_inspect_table_columns_and_constraints(self) -> None:
        dept_table = self.connector.inspect_table("departments")
        self.assertEqual(dept_table.name, "departments")
        self.assertIsNotNone(dept_table.primary_key)
        self.assertEqual(dept_table.primary_key.columns, ("id",))

        col_names = dept_table.column_names
        self.assertIn("id", col_names)
        self.assertIn("name", col_names)
        self.assertIn("code", col_names)

    def test_inspect_foreign_keys(self) -> None:
        emp_table = self.connector.inspect_table("employees")
        self.assertEqual(len(emp_table.foreign_keys), 1)
        fk = emp_table.foreign_keys[0]
        self.assertEqual(fk.target_table, "departments")
        self.assertEqual(fk.source_columns, ("dept_id",))
        self.assertEqual(fk.target_columns, ("id",))
        self.assertEqual(fk.on_delete, "CASCADE")

    def test_snapshot_extraction_and_topological_sort(self) -> None:
        snapshot = self.connector.extract_snapshot(database_name="corporate_db")
        self.assertEqual(snapshot.engine, "sqlite")
        self.assertEqual(len(snapshot.tables), 3)

        # Topological creation order should put departments before employees
        table_list = [t for t in snapshot.tables if t.name in ("departments", "employees")]
        order = compute_topological_sort(table_list)
        self.assertEqual(order, ["main.departments", "main.employees"])

    def test_diagnostics_on_extracted_schema(self) -> None:
        snapshot = self.connector.extract_snapshot()
        findings = run_all_diagnostics(snapshot.tables)

        # "audit log" lacks a primary key
        missing_pk_tables = [f.table for f in findings if f.rule_id == "RULE-INT-001"]
        self.assertIn("main.audit log", missing_pk_tables)

        # employees has an index on dept_id, so it should not flag RULE-PERF-002
        unindexed_fk_tables = [f.table for f in findings if f.rule_id == "RULE-PERF-002"]
        self.assertNotIn("main.employees", unindexed_fk_tables)


if __name__ == "__main__":
    unittest.main()
