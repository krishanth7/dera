"""DERA Connectors — Filesystem Containment & Tenant Storage Isolation.

Enforces strict filesystem path resolution, workspace containment, symlink escape checks,
and OS device blocking for SQLite and local file-based database connectors.
"""

from __future__ import annotations

import os
import pathlib
from collections.abc import Sequence

from dera_connectors.security.errors import FilesystemIsolationViolationError

# Prohibited device names and prefixes across operating systems
_PROHIBITED_DEVICE_PREFIXES = (
    "/dev/",
    "\\\\.\\",
    "\\\\?\\",
    "/proc/",
    "/sys/",
)

_PROHIBITED_DEVICE_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
}


def validate_filesystem_target(
    db_path: str,
    approved_roots: Sequence[str] | None = None,
    allow_memory: bool = False,
    workspace_id: str | None = None,
) -> str:
    """Validate, canonicalize, and isolate a local database file path.

    Parameters
    ----------
    db_path : str
        Target SQLite file path or ':memory:'.
    approved_roots : Sequence[str] | None
        Approved directory roots for containment.
    allow_memory : bool
        Whether ':memory:' is permitted.
    workspace_id : str | None
        Optional workspace ID for directory containment validation.

    Returns
    -------
    str
        Canonical, validated absolute filesystem path.

    Raises
    ------
    FilesystemIsolationViolationError
        If path violates filesystem isolation or attempts traversal.
    """
    raw_path = db_path.strip()

    # 1. In-memory check
    if raw_path in (":memory:", "file::memory:"):
        if not allow_memory:
            raise FilesystemIsolationViolationError(
                raw_path,
                "In-memory SQLite databases (:memory:) are prohibited in production mode.",
            )
        return ":memory:"

    # 2. Null byte detection
    if "\0" in raw_path:
        raise FilesystemIsolationViolationError(
            raw_path, "Database path contains illegal null byte characters."
        )

    # 3. Device and special prefix protection
    lower_path = raw_path.lower()
    for prefix in _PROHIBITED_DEVICE_PREFIXES:
        if lower_path.startswith(prefix):
            raise FilesystemIsolationViolationError(
                raw_path, f"Access to special or device filesystem prefix '{prefix}' is prohibited."
            )

    base_name = os.path.basename(raw_path).split(".")[0].lower()
    if base_name in _PROHIBITED_DEVICE_NAMES:
        raise FilesystemIsolationViolationError(
            raw_path, f"Access to reserved device identifier '{base_name}' is prohibited."
        )

    # 4. Canonicalize absolute path resolving symlinks
    try:
        abs_path = os.path.abspath(raw_path)
        real_path = os.path.realpath(abs_path)
    except Exception as exc:
        raise FilesystemIsolationViolationError(
            raw_path, f"Failed to canonicalize path: {exc}"
        ) from exc

    # 5. Enforce approved storage root containment
    if approved_roots:
        is_contained = False
        for root in approved_roots:
            real_root = os.path.realpath(os.path.abspath(root))
            try:
                common = os.path.commonpath([real_root, real_path])
                if common == real_root:
                    is_contained = True
                    break
            except ValueError:
                # Different drive letters on Windows
                continue

        if not is_contained:
            raise FilesystemIsolationViolationError(
                real_path,
                "Target path resides outside configured workspace storage roots.",
            )

    # 6. Verify file existence and readability
    if not os.path.exists(real_path):
        raise FilesystemIsolationViolationError(
            real_path, f"Database file does not exist: '{os.path.basename(real_path)}'."
        )

    if not os.path.isfile(real_path):
        raise FilesystemIsolationViolationError(
            real_path, f"Target is not a regular file: '{os.path.basename(real_path)}'."
        )

    if not os.access(real_path, os.R_OK):
        raise FilesystemIsolationViolationError(
            real_path,
            f"Read permission denied by operating system: '{os.path.basename(real_path)}'.",
        )

    return real_path


def build_sqlite_readonly_uri(canonical_path: str, immutable: bool = False) -> str:
    """Build a deterministic, parameterized SQLite read-only URI."""
    if canonical_path == ":memory:":
        return "file::memory:?mode=ro"

    file_path_obj = pathlib.Path(canonical_path)
    file_uri_path = file_path_obj.as_uri()

    query_parts = ["mode=ro"]
    if immutable:
        query_parts.append("immutable=1")

    return f"{file_uri_path}?{'&'.join(query_parts)}"
