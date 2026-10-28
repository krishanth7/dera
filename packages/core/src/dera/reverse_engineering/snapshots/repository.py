"""DERA Reverse Engineering — Phase 6.5 Snapshot Storage Implementations.

Provides production-ready SnapshotStorage implementations:
1. InMemorySnapshotStorage: In-memory store with content-addressable deduplication and workspace isolation.
2. FileSystemSnapshotStorage: File-system persistence with atomic writes, path traversal protection,
   and checksum verification.
"""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path

from dera.reverse_engineering.snapshots.errors import (
    SnapshotNotFoundError,
    SnapshotStorageError,
    SnapshotUnauthorizedError,
)
from dera.reverse_engineering.snapshots.integrity import (
    SnapshotIntegrityReport,
    verify_snapshot_integrity,
)
from dera.reverse_engineering.snapshots.models import (
    SchemaSnapshot,
    SnapshotEnvelope,
    SnapshotStructuralPayload,
)
from dera.reverse_engineering.snapshots.serialization import (
    deserialize_snapshot_from_json,
    serialize_snapshot_to_json,
)
from dera.reverse_engineering.snapshots.storage import (
    SnapshotFilter,
    SnapshotStorage,
)

SAFE_WORKSPACE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,128}$")


def _sanitize_workspace_id(workspace_id: str) -> str:
    """Ensure workspace identifier does not contain path traversal characters."""
    if not SAFE_WORKSPACE_ID_REGEX.match(workspace_id) or ".." in workspace_id:
        raise SnapshotUnauthorizedError(
            f"Invalid or unsafe workspace identifier: '{workspace_id}'."
        )
    return workspace_id


class InMemorySnapshotStorage(SnapshotStorage):
    """In-memory SnapshotStorage with content-addressable structural deduplication.

    Structural payloads are deduplicated across identical fingerprints, while separate
    snapshot envelopes and workspace ownership boundaries are maintained.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        # workspace_id -> {snapshot_id: (envelope, fingerprint)}
        self._envelopes: dict[str, dict[str, tuple[SnapshotEnvelope, str, str, str, str]]] = {}
        # fingerprint -> SnapshotStructuralPayload
        self._payloads: dict[str, SnapshotStructuralPayload] = {}

    async def save(self, snapshot: SchemaSnapshot) -> None:
        """Persist a SchemaSnapshot into memory."""
        async with self._lock:
            ws_id = snapshot.workspace_id
            if ws_id not in self._envelopes:
                self._envelopes[ws_id] = {}

            # Immutability check
            if snapshot.snapshot_id in self._envelopes[ws_id]:
                _, existing_fp, _, _, _ = self._envelopes[ws_id][snapshot.snapshot_id]
                if existing_fp != snapshot.fingerprint:
                    raise SnapshotStorageError(
                        f"Cannot overwrite immutable snapshot '{snapshot.snapshot_id}' with different content."
                    )
                return  # Identical snapshot already stored

            # Store structural payload (content-addressable deduplication)
            self._payloads[snapshot.fingerprint] = snapshot.payload

            # Store envelope
            self._envelopes[ws_id][snapshot.snapshot_id] = (
                snapshot.envelope,
                snapshot.fingerprint,
                snapshot.format_version,
                snapshot.fingerprint_algorithm,
                snapshot.fingerprint_domain,
            )

    async def get_by_id(self, snapshot_id: str, workspace_id: str) -> SchemaSnapshot | None:
        """Retrieve a snapshot by ID within the workspace."""
        async with self._lock:
            ws_records = self._envelopes.get(workspace_id)
            if not ws_records or snapshot_id not in ws_records:
                return None

            envelope, fp, fmt_ver, algo, domain = ws_records[snapshot_id]
            payload = self._payloads.get(fp)
            if payload is None:
                return None

            return SchemaSnapshot(
                format_version=fmt_ver,
                snapshot_id=envelope.snapshot_id,
                fingerprint=fp,
                fingerprint_algorithm=algo,
                fingerprint_domain=domain,
                envelope=envelope,
                payload=payload,
            )

    async def get_by_fingerprint(
        self,
        fingerprint: str,
        workspace_id: str,
    ) -> list[SchemaSnapshot]:
        """Retrieve all snapshots matching a structural fingerprint within a workspace."""
        async with self._lock:
            ws_records = self._envelopes.get(workspace_id)
            if not ws_records:
                return []

            results: list[SchemaSnapshot] = []
            payload = self._payloads.get(fingerprint)
            if payload is None:
                return []

            for snap_id, (envelope, fp, fmt_ver, algo, domain) in ws_records.items():
                if fp == fingerprint:
                    results.append(
                        SchemaSnapshot(
                            format_version=fmt_ver,
                            snapshot_id=snap_id,
                            fingerprint=fp,
                            fingerprint_algorithm=algo,
                            fingerprint_domain=domain,
                            envelope=envelope,
                            payload=payload,
                        )
                    )
            return results

    async def list_snapshots(self, filter_params: SnapshotFilter) -> list[SchemaSnapshot]:
        """List snapshots matching filter criteria within the authorized workspace."""
        async with self._lock:
            ws_records = self._envelopes.get(filter_params.workspace_id)
            if not ws_records:
                return []

            matched: list[SchemaSnapshot] = []
            for snap_id, (envelope, fp, fmt_ver, algo, domain) in ws_records.items():
                payload = self._payloads.get(fp)
                if payload is None:
                    continue

                # Apply filters
                if (
                    filter_params.database_name
                    and payload.database_name != filter_params.database_name
                ):
                    continue
                if filter_params.engine and payload.engine != filter_params.engine:
                    continue
                if (
                    filter_params.structural_fingerprint
                    and fp != filter_params.structural_fingerprint
                ):
                    continue
                if (
                    filter_params.completeness
                    and payload.completeness != filter_params.completeness
                ):
                    continue
                if filter_params.tag_key:
                    if filter_params.tag_key not in envelope.tags:
                        continue
                    if (
                        filter_params.tag_value
                        and envelope.tags[filter_params.tag_key] != filter_params.tag_value
                    ):
                        continue
                if (
                    filter_params.created_after
                    and envelope.capture_timestamp < filter_params.created_after
                ):
                    continue
                if (
                    filter_params.created_before
                    and envelope.capture_timestamp > filter_params.created_before
                ):
                    continue

                matched.append(
                    SchemaSnapshot(
                        format_version=fmt_ver,
                        snapshot_id=snap_id,
                        fingerprint=fp,
                        fingerprint_algorithm=algo,
                        fingerprint_domain=domain,
                        envelope=envelope,
                        payload=payload,
                    )
                )

            # Sort deterministically by capture_timestamp desc, then snapshot_id
            matched.sort(key=lambda s: (s.envelope.capture_timestamp, s.snapshot_id), reverse=True)

            # Slice pagination
            start = filter_params.offset
            end = start + filter_params.limit
            return matched[start:end]

    async def delete(self, snapshot_id: str, workspace_id: str) -> bool:
        """Authorized deletion of a snapshot record."""
        async with self._lock:
            ws_records = self._envelopes.get(workspace_id)
            if not ws_records or snapshot_id not in ws_records:
                return False

            envelope, fp, _, _, _ = ws_records.pop(snapshot_id)

            # Clean up payload if no other snapshot references it
            is_referenced = any(
                fp == record_fp
                for records in self._envelopes.values()
                for _, record_fp, _, _, _ in records.values()
            )
            if not is_referenced:
                self._payloads.pop(fp, None)

            return True

    async def verify(self, snapshot_id: str, workspace_id: str) -> SnapshotIntegrityReport:
        """Verify the integrity of a stored snapshot."""
        snapshot = await self.get_by_id(snapshot_id, workspace_id)
        if snapshot is None:
            raise SnapshotNotFoundError(snapshot_id, workspace_id)
        return verify_snapshot_integrity(snapshot)


class FileSystemSnapshotStorage(SnapshotStorage):
    """File-system based SnapshotStorage enforcing atomic writes and workspace directory isolation."""

    def __init__(self, base_directory: Path | str) -> None:
        self.base_dir = Path(base_directory).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def _get_workspace_dir(self, workspace_id: str) -> Path:
        """Resolve and validate the workspace directory path."""
        sanitized = _sanitize_workspace_id(workspace_id)
        ws_dir = (self.base_dir / sanitized).resolve()
        # Path traversal guard
        if not str(ws_dir).startswith(str(self.base_dir)):
            raise SnapshotUnauthorizedError(
                f"Path traversal detected for workspace '{workspace_id}'."
            )
        ws_dir.mkdir(parents=True, exist_ok=True)
        return ws_dir

    def _get_snapshot_path(self, workspace_id: str, snapshot_id: str) -> Path:
        """Resolve the file path for a snapshot within a workspace."""
        ws_dir = self._get_workspace_dir(workspace_id)
        if not re.match(r"^[a-zA-Z0-9_\-]{1,64}$", snapshot_id):
            raise SnapshotStorageError(f"Invalid snapshot identifier '{snapshot_id}'.")
        target_file = (ws_dir / f"{snapshot_id}.json").resolve()
        if not str(target_file).startswith(str(ws_dir)):
            raise SnapshotUnauthorizedError(
                f"Path traversal detected for snapshot '{snapshot_id}'."
            )
        return target_file

    async def save(self, snapshot: SchemaSnapshot) -> None:
        """Persist a SchemaSnapshot atomically to disk."""
        target_path = self._get_snapshot_path(snapshot.workspace_id, snapshot.snapshot_id)

        # Check immutability
        if target_path.exists():
            content = await asyncio.to_thread(target_path.read_text, encoding="utf-8")
            existing = deserialize_snapshot_from_json(content)
            if existing.fingerprint != snapshot.fingerprint:
                raise SnapshotStorageError(
                    f"Cannot overwrite immutable snapshot '{snapshot.snapshot_id}' with different content."
                )
            return

        json_content = serialize_snapshot_to_json(snapshot, indent=2)
        tmp_path = target_path.with_suffix(".tmp")

        async with self._lock:
            # Write to temporary file and atomically replace
            await asyncio.to_thread(tmp_path.write_text, json_content, encoding="utf-8")
            await asyncio.to_thread(os.replace, tmp_path, target_path)

    async def get_by_id(self, snapshot_id: str, workspace_id: str) -> SchemaSnapshot | None:
        """Retrieve a snapshot from disk by ID."""
        target_path = self._get_snapshot_path(workspace_id, snapshot_id)
        if not target_path.exists():
            return None

        content = await asyncio.to_thread(target_path.read_text, encoding="utf-8")
        return deserialize_snapshot_from_json(content)

    async def get_by_fingerprint(
        self,
        fingerprint: str,
        workspace_id: str,
    ) -> list[SchemaSnapshot]:
        """Retrieve snapshots matching a structural fingerprint within a workspace."""
        ws_dir = self._get_workspace_dir(workspace_id)
        matches: list[SchemaSnapshot] = []

        files = await asyncio.to_thread(lambda: list(ws_dir.glob("*.json")))
        for f in files:
            content = await asyncio.to_thread(f.read_text, encoding="utf-8")
            try:
                snap = deserialize_snapshot_from_json(content)
                if snap.fingerprint == fingerprint:
                    matches.append(snap)
            except Exception:
                continue

        return matches

    async def list_snapshots(self, filter_params: SnapshotFilter) -> list[SchemaSnapshot]:
        """List and filter snapshots in workspace directory."""
        ws_dir = self._get_workspace_dir(filter_params.workspace_id)
        files = await asyncio.to_thread(lambda: list(ws_dir.glob("*.json")))

        matched: list[SchemaSnapshot] = []
        for f in files:
            content = await asyncio.to_thread(f.read_text, encoding="utf-8")
            try:
                snap = deserialize_snapshot_from_json(content)
            except Exception:
                continue

            if filter_params.database_name and snap.database_name != filter_params.database_name:
                continue
            if filter_params.engine and snap.engine != filter_params.engine:
                continue
            if (
                filter_params.structural_fingerprint
                and snap.fingerprint != filter_params.structural_fingerprint
            ):
                continue
            if filter_params.completeness and snap.completeness != filter_params.completeness:
                continue
            if filter_params.tag_key:
                if filter_params.tag_key not in snap.envelope.tags:
                    continue
                if (
                    filter_params.tag_value
                    and snap.envelope.tags[filter_params.tag_key] != filter_params.tag_value
                ):
                    continue
            if (
                filter_params.created_after
                and snap.envelope.capture_timestamp < filter_params.created_after
            ):
                continue
            if (
                filter_params.created_before
                and snap.envelope.capture_timestamp > filter_params.created_before
            ):
                continue

            matched.append(snap)

        matched.sort(key=lambda s: (s.envelope.capture_timestamp, s.snapshot_id), reverse=True)
        start = filter_params.offset
        end = start + filter_params.limit
        return matched[start:end]

    async def delete(self, snapshot_id: str, workspace_id: str) -> bool:
        """Authorized deletion of snapshot file."""
        target_path = self._get_snapshot_path(workspace_id, snapshot_id)
        if not target_path.exists():
            return False

        async with self._lock:
            await asyncio.to_thread(target_path.unlink, missing_ok=True)
            return True

    async def verify(self, snapshot_id: str, workspace_id: str) -> SnapshotIntegrityReport:
        """Verify integrity of on-disk snapshot file."""
        snapshot = await self.get_by_id(snapshot_id, workspace_id)
        if snapshot is None:
            raise SnapshotNotFoundError(snapshot_id, workspace_id)
        return verify_snapshot_integrity(snapshot)
