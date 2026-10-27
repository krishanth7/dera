"""DERA SQLite Connector — Filesystem Isolation & Path Traversal Guards.

Implements strict filesystem validation, canonical path resolution, symlink boundary
enforcement, and deterministic read-only SQLite URI generation.
"""

from __future__ import annotations

import os
import pathlib

from dera_connectors.errors import (
    ConnectorInvalidConfigurationError,
    ConnectorPermissionDeniedError,
    ConnectorSecurityViolationError,
    ConnectorUnavailableError,
)

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


def validate_sqlite_path(
    db_path: str,
    approved_roots: list[str] | None = None,
    allow_memory: bool = False,
) -> str:
    """Validate and canonicalize a SQLite database file path.

    Parameters
    ----------
    db_path : str
        Target SQLite database path or ':memory:'.
    approved_roots : list[str] | None
        Optional whitelist of approved root directories for workspace containment.
    allow_memory : bool
        Whether in-memory database strings are allowed.

    Returns
    -------
    str
        Canonical, validated absolute filesystem path or ':memory:'.

    Raises
    ------
    ConnectorInvalidConfigurationError
        If path is malformed, contains null bytes, or represents a prohibited device.
    ConnectorSecurityViolationError
        If path traverses outside approved roots or resolves via an unsafe symlink.
    ConnectorUnavailableError
        If the file does not exist or is not a regular file.
    ConnectorPermissionDeniedError
        If read access is denied by operating system permissions.
    """
    raw_path = db_path.strip()

    # In-memory database check
    if raw_path in (":memory:", "file::memory:"):
        if not allow_memory:
            raise ConnectorSecurityViolationError(
                "In-memory SQLite databases (:memory:) are prohibited in production mode. "
                "Configure a valid workspace database file.",
                details={"target": ":memory:"},
            )
        return ":memory:"

    # Null byte detection
    if "\0" in raw_path:
        raise ConnectorInvalidConfigurationError(
            "SQLite database path contains forbidden null byte characters.",
            details={"raw_length": len(raw_path)},
        )

    # Device and special path protection
    lower_path = raw_path.lower()
    for prefix in _PROHIBITED_DEVICE_PREFIXES:
        if lower_path.startswith(prefix):
            raise ConnectorSecurityViolationError(
                f"Access to special or device filesystem prefix '{prefix}' is strictly prohibited.",
                details={"prefix": prefix},
            )

    base_name = os.path.basename(raw_path).split(".")[0].lower()
    if base_name in _PROHIBITED_DEVICE_NAMES:
        raise ConnectorSecurityViolationError(
            f"Access to reserved device identifier '{base_name}' is prohibited.",
            details={"reserved_name": base_name},
        )

    # Canonicalize absolute path resolving symlinks
    try:
        abs_path = os.path.abspath(raw_path)
        real_path = os.path.realpath(abs_path)
    except Exception as exc:
        raise ConnectorInvalidConfigurationError(
            f"Failed to resolve SQLite path '{raw_path}': {exc}",
            details={"path": raw_path},
        ) from exc

    # Enforce approved storage root containment
    if approved_roots:
        is_contained = False
        for root in approved_roots:
            real_root = os.path.realpath(os.path.abspath(root))
            try:
                # Check path containment using commonpath
                common = os.path.commonpath([real_root, real_path])
                if common == real_root:
                    is_contained = True
                    break
            except ValueError:
                # Different drives on Windows
                continue

        if not is_contained:
            raise ConnectorSecurityViolationError(
                "Access denied: SQLite database path resides outside approved workspace storage roots.",
                details={"target": os.path.basename(real_path)},
            )

    # Verify file existence and type
    if not os.path.exists(real_path):
        raise ConnectorUnavailableError(
            f"SQLite database file not found: '{os.path.basename(real_path)}'.",
            details={"file": os.path.basename(real_path)},
        )

    if not os.path.isfile(real_path):
        raise ConnectorInvalidConfigurationError(
            f"SQLite target is not a regular file: '{os.path.basename(real_path)}'.",
            details={"target": os.path.basename(real_path)},
        )

    # Verify file read permissions
    if not os.access(real_path, os.R_OK):
        raise ConnectorPermissionDeniedError(
            f"Operating system read permission denied for SQLite database: '{os.path.basename(real_path)}'.",
            details={"file": os.path.basename(real_path)},
        )

    return real_path


def build_sqlite_readonly_uri(canonical_path: str, immutable: bool = False) -> str:
    """Build a deterministic, parameterized SQLite read-only URI.

    Parameters
    ----------
    canonical_path : str
        Canonicalized filesystem path or ':memory:'.
    immutable : bool
        Whether to attach immutable=1 query flag.

    Returns
    -------
    str
        Properly escaped SQLite URI string.
    """
    if canonical_path == ":memory:":
        return "file::memory:?mode=ro"

    # Convert Windows / POSIX path to standard file URI path
    file_path_obj = pathlib.Path(canonical_path)
    file_uri_path = file_path_obj.as_uri()

    # Append mode=ro
    query_parts = ["mode=ro"]
    if immutable:
        query_parts.append("immutable=1")

    query_str = "&".join(query_parts)
    return f"{file_uri_path}?{query_str}"
