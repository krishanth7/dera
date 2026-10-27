# DERA SQLite Filesystem Isolation & Path Security

## Threat Model

When inspecting local SQLite database files, malicious or untrusted input could attempt:
1. **Directory Traversal (`../` or `..\`):** Accessing host operating system files (e.g. `/etc/passwd`, `C:\Windows\System32`, or `.env` application secrets).
2. **Symlink Redirection:** Placing a symlink in an approved directory that resolves to sensitive host files outside the sandbox.
3. **Arbitrary URI Parameter Injection:** Adding query parameters (e.g. `mode=rwc`, `vfs=...`, `nolock=1`) into SQLite connection strings.
4. **Denial of Service (Oversized Files / Infinite Devices):** Connecting to `/dev/zero`, `/dev/random`, or multi-terabyte files.

---

## Defensive Countermeasures

### 1. Prohibited Paths & Patterns

`validate_sqlite_path` in `packages/connectors/src/dera_connectors/sqlite/filesystem.py` rejects:
- Null bytes (`\0`) in paths.
- Paths starting with or resolving to system directories:
  - Linux/Unix: `/etc`, `/sys`, `/proc`, `/dev`, `/root`, `/var/run`, `/boot`.
  - Windows: `C:\Windows`, `C:\Program Files`, `C:\ProgramData`.
- Hidden configuration directories (`.env`, `.git`, `.ssh`, `.aws`, `.config`).

### 2. Canonicalization & Storage Root Validation

1. `os.path.realpath` resolves all symbolic links and normalizes path separators.
2. If `approved_storage_roots` are configured, the resolved realpath must have an approved root as its prefix (`os.path.commonpath([resolved, root]) == root`).
3. If the path escapes the approved storage root, `ConnectorSecurityViolationError` is raised immediately.

### 3. Safe URI Construction

`build_sqlite_readonly_uri` safely encodes canonical file paths using RFC 3986 `pathlib.Path.as_uri()` and appends trusted parameters only:
```text
file:///var/data/workspaces/app.db?mode=ro
```
Untrusted query parameters provided by callers are rejected and never concatenated into SQLite URIs.
