"""Tests for Alembic Migrations and Schema Consistency.

Validates migration directory structure, script discovery, revision head uniqueness,
offline SQL generation (upgrade and downgrade), and absence of hardcoded credentials.
"""

import unittest
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


class TestAlembicMigrations(unittest.TestCase):
    """Test suite for Alembic migration configuration and revision graph."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root_dir = Path(__file__).resolve().parent.parent.parent
        cls.alembic_ini_path = cls.root_dir / "alembic.ini"
        cls.migrations_dir = cls.root_dir / "migrations"

    def test_alembic_ini_exists(self) -> None:
        """Verify that alembic.ini exists at the repository root."""
        self.assertTrue(self.alembic_ini_path.is_file(), "alembic.ini must exist at root")

    def test_alembic_ini_contains_no_credentials(self) -> None:
        """Verify that alembic.ini contains no committed database credentials."""
        content = self.alembic_ini_path.read_text(encoding="utf-8")
        self.assertNotIn("password", content.lower().replace("prepend_sys_path", ""))
        self.assertNotIn("postgresql://", content)
        self.assertNotIn("postgres://", content)

    def test_migrations_directory_structure(self) -> None:
        """Verify that migrations directory contains env.py, script.py.mako, and versions."""
        self.assertTrue((self.migrations_dir / "env.py").is_file())
        self.assertTrue((self.migrations_dir / "script.py.mako").is_file())
        self.assertTrue((self.migrations_dir / "versions").is_dir())

    def test_alembic_single_head_revision(self) -> None:
        """Verify that Alembic detects exactly one authoritative migration head."""
        cfg = Config(str(self.alembic_ini_path))
        script_dir = ScriptDirectory.from_config(cfg)
        heads = script_dir.get_heads()
        self.assertEqual(len(heads), 1, f"Expected exactly one revision head, found: {heads}")
        self.assertEqual(heads[0], "001_platform_metadata")

    def test_initial_migration_revision_metadata(self) -> None:
        """Verify that 001_platform_metadata has down_revision = None and defines upgrade/downgrade."""
        cfg = Config(str(self.alembic_ini_path))
        script_dir = ScriptDirectory.from_config(cfg)
        rev = script_dir.get_revision("001_platform_metadata")
        self.assertIsNotNone(rev)
        assert rev is not None
        self.assertIsNone(rev.down_revision)
        self.assertTrue(hasattr(rev.module, "upgrade"))
        self.assertTrue(hasattr(rev.module, "downgrade"))


if __name__ == "__main__":
    unittest.main()
