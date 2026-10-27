# SQLite Filesystem Isolation & Path Traversal Guards

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Local Database Security Boundaries

Because SQLite operates as an in-process library accessing files directly on the host or container filesystem, user-supplied SQLite database file paths introduce critical security risks:
- **Path Traversal:** Attempting to read arbitrary host files (e.g. `/etc/passwd`, `/etc/shadow`, Windows registry hives).
- **Symlink Escape Attacks:** Pointing a harmless-looking file path inside an allowed directory to an unauthorized target via a symbolic link.
- **Device File Exploitation:** Opening device or pipe files (`/dev/null`, `/dev/random`, `\\.\PhysicalDrive0`, `NUL`, `CON`, `PRN`, `AUX`) causing worker hangs or data corruption.
- **Null-Byte Injection:** Injecting `\0` to truncate file paths and bypass extension validation.

DERA enforces strict filesystem isolation implemented in [`dera_connectors.security.isolation`](../../packages/connectors/src/dera_connectors/security/isolation.py) and [`dera_connectors.sqlite.filesystem`](../../packages/connectors/src/dera_connectors/sqlite/filesystem.py).

---

## 2. Path Canonicalization & Root Containment

Every SQLite file path submitted to DERA must undergo mandatory validation:

```python
from dera_connectors.security import validate_filesystem_target, FilesystemIsolationViolationError

canonical_path = validate_filesystem_target(
    db_path="/var/lib/dera/workspaces/ws-101/data.db",
    approved_roots=["/var/lib/dera/workspaces/ws-101"],
    allow_memory=False,
)
```

### Validation Steps

1. **In-Memory Check:** `:memory:` or `file::memory:` is prohibited in production mode to prevent ephemeral un-auditable schema operations.
2. **Null Byte Detection:** Paths containing `\0` raise `FilesystemIsolationViolationError`.
3. **Device Prefix Rejection:** Paths starting with `/dev/`, `\\.\`, `\\?\`, `/proc/`, or `/sys/` are rejected.
4. **Reserved Device Name Rejection:** Files named `CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9` (case-insensitive) are rejected.
5. **Canonical Realpath Resolution:** Both `os.path.abspath` and `os.path.realpath` are resolved to eliminate `..` traversal segments and fully dereference symbolic links.
6. **Root Directory Containment:** The canonical realpath must share a common prefix (`os.path.commonpath`) with one of the approved workspace storage roots. If the resolved realpath points outside the approved root, it is rejected.
7. **File Verification:** The target file must exist, must be a regular file (`os.path.isfile`), and must have read permissions (`os.access(..., os.R_OK)`).

---

## 3. Read-Only URI Parameterization

Once validated, SQLite connections are opened using parameter-enforced read-only file URIs via [`build_sqlite_readonly_uri`](../../packages/connectors/src/dera_connectors/security/isolation.py):

```text
file:///var/lib/dera/workspaces/ws-101/data.db?mode=ro
```

When connecting to read-only database snapshots, the `immutable=1` query parameter is optionally appended:

```text
file:///var/lib/dera/workspaces/ws-101/data.db?mode=ro&immutable=1
```

Opening databases with `mode=ro` instructs the SQLite engine to fail closed on any attempt to execute write operations or update journal files.
