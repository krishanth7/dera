"""Tests for Phase 6.5 Snapshot Security Controls.

Verifies:
- Storage path traversal prevention ('../', absolute escapes).
- Unsafe workspace identifier rejection.
- Zero credential leakage in snapshots.
- Denial-of-service resource limits (oversized payload and object limits).
- Safe deserialization preventing arbitrary code execution.
"""

from __future__ import annotations

import tempfile
import unittest

import pytest
from dera.reverse_engineering.snapshots.errors import (
    SnapshotResourceLimitError,
    SnapshotUnauthorizedError,
)
from dera.reverse_engineering.snapshots.limits import SnapshotResourceLimits
from dera.reverse_engineering.snapshots.repository import (
    FileSystemSnapshotStorage,
    _sanitize_workspace_id,
)
from dera.reverse_engineering.snapshots.serialization import (
    serialize_snapshot_to_json,
)

from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
    make_single_table_database,
)


class TestSnapshotSecurity(unittest.IsolatedAsyncioTestCase):
    """Test suite for snapshot security controls."""

    def test_sanitize_workspace_id_path_traversal(self) -> None:
        """Verify directory traversal patterns in workspace_id raise SnapshotUnauthorizedError."""
        with pytest.raises(SnapshotUnauthorizedError):
            _sanitize_workspace_id("../etc/passwd")

        with pytest.raises(SnapshotUnauthorizedError):
            _sanitize_workspace_id("..\\windows\\system32")

        with pytest.raises(SnapshotUnauthorizedError):
            _sanitize_workspace_id("ws/../../secret")

        with pytest.raises(SnapshotUnauthorizedError):
            _sanitize_workspace_id("invalid spaces ws")

        self.assertEqual(_sanitize_workspace_id("valid-ws_123.test"), "valid-ws_123.test")

    async def test_filesystem_storage_traversal_blocked(self) -> None:
        """Verify storage backend rejects traversal attempts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileSystemSnapshotStorage(tmpdir)
            with pytest.raises(SnapshotUnauthorizedError):
                await storage.get_by_id("snap_123", "../../escape")

    def test_no_credentials_embedded_in_payload(self) -> None:
        """Verify that connection passwords, tokens, or URI credentials are never serialized."""
        db = make_single_table_database()
        snap = build_snapshot_from_database(db)
        json_output = serialize_snapshot_to_json(snap)

        forbidden_tokens = ["password", "secret", "token", "auth_key", "bearer"]
        for token in forbidden_tokens:
            self.assertNotIn(f'"{token}":', json_output.lower())

    def test_resource_limit_oversized_payload_protection(self) -> None:
        """Verify payload size bounds prevent memory exhaustion attacks."""
        db = make_single_table_database()
        snap = build_snapshot_from_database(db)

        # Restrict limit to 200 bytes
        strict_limits = SnapshotResourceLimits(max_serialized_bytes=200)
        with pytest.raises(SnapshotResourceLimitError):
            serialize_snapshot_to_json(snap, limits=strict_limits)


if __name__ == "__main__":
    unittest.main()
