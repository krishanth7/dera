"""DERA Reverse Engineering — Phase 6.5 Snapshot Resource Limits.

Defines bounded operational limits for snapshot payload sizes, object counts,
string lengths, and serialization bounds to prevent resource exhaustion and DoS.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SnapshotResourceLimits:
    """Configurable resource bounds for schema snapshot generation, storage, and deserialization."""

    max_snapshot_size_bytes: int = 50 * 1024 * 1024  # 50 MB
    max_object_count: int = 100_000
    max_nesting_depth: int = 32
    max_identifier_length: int = 1024
    max_sql_expression_bytes: int = 65_536  # 64 KB
    max_serialized_bytes: int = 50 * 1024 * 1024  # 50 MB
    max_storage_operation_duration_seconds: float = 30.0
