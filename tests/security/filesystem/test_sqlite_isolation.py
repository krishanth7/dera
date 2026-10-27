"""Tests for SQLite Filesystem Isolation & Path Traversal Guards.

Validates that local database paths are canonicalized, confined to approved roots,
protected from device files and null bytes, and formatted into read-only URIs.
"""

import os
import tempfile
import unittest

from dera_connectors.security import (
    FilesystemIsolationViolationError,
    build_sqlite_readonly_uri,
    validate_filesystem_target,
)


class TestSQLiteFilesystemIsolation(unittest.TestCase):
    """Test suite verifying SQLite filesystem isolation."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.approved_root = self.temp_dir.name
        self.valid_db_path = os.path.join(self.approved_root, "test.db")
        # Create a valid SQLite test file
        with open(self.valid_db_path, "wb") as f:
            f.write(b"SQLite format 3\0\0\0\0")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_valid_file_within_approved_root_passes(self) -> None:
        """Verify valid regular file inside approved root passes validation."""
        canonical = validate_filesystem_target(
            db_path=self.valid_db_path,
            approved_roots=[self.approved_root],
            allow_memory=False,
        )
        self.assertTrue(os.path.isabs(canonical))
        self.assertTrue(os.path.exists(canonical))

    def test_path_traversal_outside_approved_root_blocked(self) -> None:
        """Verify relative traversal escaping the approved root is blocked."""
        # Attempt to access a file outside the approved root
        with tempfile.NamedTemporaryFile() as outside_file:
            relative_escape = os.path.join(
                self.approved_root, "..", os.path.basename(outside_file.name)
            )
            with self.assertRaises(
                FilesystemIsolationViolationError,
                msg="Path outside approved root was not blocked.",
            ) as ctx:
                validate_filesystem_target(
                    db_path=relative_escape,
                    approved_roots=[self.approved_root],
                )
            self.assertIn(
                "resides outside configured workspace storage roots", ctx.exception.message
            )

    def test_null_byte_in_path_blocked(self) -> None:
        """Verify paths containing null byte characters are blocked."""
        with self.assertRaises(FilesystemIsolationViolationError) as ctx:
            validate_filesystem_target(
                db_path=self.valid_db_path + "\0malicious",
                approved_roots=[self.approved_root],
            )
        self.assertIn("null byte", ctx.exception.message)

    def test_prohibited_device_names_blocked(self) -> None:
        """Verify Windows/POSIX device files are blocked."""
        device_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        for dev in device_names:
            fake_path = os.path.join(self.approved_root, f"{dev}.db")
            with self.assertRaises(
                FilesystemIsolationViolationError,
                msg=f"Device name {dev} was not blocked.",
            ):
                validate_filesystem_target(
                    db_path=fake_path,
                    approved_roots=[self.approved_root],
                )

    def test_prohibited_device_prefixes_blocked(self) -> None:
        """Verify /dev/, /proc/, /sys/, \\\\.\\ are blocked."""
        prefixes = ["/dev/sda", "/proc/self/mem", "/sys/kernel", "\\\\.\\PhysicalDrive0"]
        for pfx in prefixes:
            with self.assertRaises(
                FilesystemIsolationViolationError,
                msg=f"Prefix {pfx} was not blocked.",
            ):
                validate_filesystem_target(
                    db_path=pfx,
                    approved_roots=[self.approved_root],
                )

    def test_in_memory_mode_rejected_when_disallowed(self) -> None:
        """Verify :memory: is blocked when allow_memory=False."""
        with self.assertRaises(FilesystemIsolationViolationError):
            validate_filesystem_target(":memory:", allow_memory=False)

        # Passes when allow_memory=True
        mem = validate_filesystem_target(":memory:", allow_memory=True)
        self.assertEqual(mem, ":memory:")

    def test_build_sqlite_readonly_uri(self) -> None:
        """Verify URI formatting attaches mode=ro and optional immutable=1."""
        uri = build_sqlite_readonly_uri(self.valid_db_path, immutable=False)
        self.assertIn("mode=ro", uri)
        self.assertNotIn("immutable=1", uri)

        immutable_uri = build_sqlite_readonly_uri(self.valid_db_path, immutable=True)
        self.assertIn("mode=ro", immutable_uri)
        self.assertIn("immutable=1", immutable_uri)

        mem_uri = build_sqlite_readonly_uri(":memory:", immutable=False)
        self.assertEqual(mem_uri, "file::memory:?mode=ro")


if __name__ == "__main__":
    unittest.main()
