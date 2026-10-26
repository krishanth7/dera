# DERA Development Troubleshooting & Diagnostics Guide

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Maintainer:** Krishanth  
> **Status:** Active Knowledge Base  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Quick Diagnostic Checklist

When encountering unexpected errors in DERA development, run through this diagnostic checklist:

1. **Verify Python & Node Runtimes:**
   ```bash
   python --version   # Must be >= 3.12 (e.g. 3.12.x or 3.13.x)
   node --version     # Must be >= 20.x
   npm --version      # Must be >= 10.x
   ```
2. **Execute Unified Verification Runner:**
   ```bash
   python scripts/development/dev.py all
   ```
3. **Verify Git Branch & Status:**
   ```bash
   git status
   ```

---

## 2. Common Issues & Verified Resolutions

### 2.1 Python Environment & Dependency Issues

#### Issue: `ModuleNotFoundError: No module named 'dera'` or `'dera_connectors'`
- **Symptom:** Running tests or scripts directly fails with import errors.
- **Root Cause:** Packages under `packages/` have not been installed in editable mode in the active virtual environment.
- **Resolution:**
  ```bash
  # Ensure your virtual environment is active, then install editable package with dev dependencies:
  pip install -e ".[dev]"
  ```
- **Diagnostic Command:**
  ```bash
  python -c "import dera, dera_connectors, dera_core; print('All core modules resolved successfully!')"
  ```

#### Issue: Windows PowerShell Execution Policy Error (`Activate.ps1 cannot be loaded`)
- **Symptom:** `.venv\Scripts\Activate.ps1 : File cannot be loaded because running scripts is disabled on this system.`
- **Root Cause:** Windows default execution policy restricts unsigned PowerShell script execution.
- **Resolution:** Grant execution rights for the current user or process scope:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
  .venv\Scripts\Activate.ps1
  ```
  *(Never disable system-wide execution security permanently; use process or current user scope).*

---

### 2.2 Node.js & TypeScript Compilation Issues

#### Issue: `Cannot find module '@dera/contracts' or its corresponding type declarations`
- **Symptom:** Running `tsc` or building `apps/web` fails with unresolved contract types.
- **Root Cause:** npm workspaces have not been linked in `node_modules`.
- **Resolution:**
  ```bash
  npm install
  ```
  This creates symbolic links in the root `node_modules/@dera/contracts` pointing to `packages/contracts`.

#### Issue: `error TS2591: Cannot find name 'process'`
- **Symptom:** TypeScript compiler errors on `process.env` references.
- **Root Cause:** Ambient Node typings missing in browser-targeted workspace.
- **Resolution:** Safe ambient declaration pattern in `apps/web/src/lib/api-client.ts`:
  ```typescript
  declare const process: { env?: Record<string, string | undefined> } | undefined;
  ```

---

### 2.3 Backend API & Port Binding Issues

#### Issue: `ERROR: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`
- **Symptom:** Uvicorn fails to start the API gateway.
- **Root Cause:** Another process or previous uvicorn session is already listening on port 8000.
- **Diagnostic Command:**
  ```bash
  # On Windows (PowerShell):
  Get-NetTCPConnection -LocalPort 8000

  # On Linux / macOS:
  lsof -i :8000
  ```
- **Resolution:** Launch uvicorn on an alternative port:
  ```bash
  python -m uvicorn dera_api.main:app --host 127.0.0.1 --port 8080
  ```
  Or update `DERA_API_PORT=8080` in your local `.env`.

---

### 2.4 Database Connector & SQLite Fixture Issues

#### Issue: `ReadOnlyViolationError: Query rejected by read-only connector boundary`
- **Symptom:** Test execution or connector query raises `ReadOnlyViolationError`.
- **Root Cause:** A query containing mutating keywords (`DROP`, `ALTER`, `TRUNCATE`, `INSERT`, `UPDATE`, `DELETE`, `GRANT`, `REVOKE`) was passed to a connector.
- **Resolution:** DERA connectors operate under strict read-only guarantees. Ensure your introspection logic queries catalog views (`sqlite_master`, `information_schema`, PRAGMAs) and never executes DDL or DML mutations.

#### Issue: `sqlite3.OperationalError: unable to open database file`
- **Symptom:** `SqliteConnector` fails to connect to target file.
- **Root Cause:** The specified path does not exist, or URI mode `mode=ro` failed because the file does not have read permissions.
- **Resolution:** Verify that the file exists and that the user running the process has read permissions. For in-memory testing, pass `:memory:`.

---

### 2.5 Documentation & Internationalization Link Failures

#### Issue: `validate_docs.py: Broken link to nonexistent file`
- **Symptom:** `python scripts/ci/validate_docs.py` fails in CI or local validation.
- **Root Cause:** A relative markdown link (such as linking to an invalid relative target) points to a nonexistent path or misspelled file.
- **Diagnostic Command:**
  ```bash
  python scripts/ci/validate_docs.py
  ```
- **Resolution:** Correct the relative path so it resolves from the directory containing the markdown document. Note that markdown anchors must match GitHub slugification rules.

#### Issue: `generate_language_navigation.py: Navigation out of sync`
- **Symptom:** `python scripts/docs/generate_language_navigation.py --check` exits with code 1.
- **Root Cause:** The 10-language navigation banner was modified manually in a README file or a new README was added.
- **Resolution:** Automatically regenerate and synchronize the canonical navigation banner:
  ```bash
  python scripts/docs/generate_language_navigation.py --write
  ```

---

### 2.6 GitHub Actions & CI Failures

#### Issue: `PR title does not conform to Conventional Commits`
- **Symptom:** CI check `PR Title Quality Gate` fails on GitHub.
- **Root Cause:** Pull request title does not adhere to Conventional Commits 1.0.0.
- **Diagnostic Command:**
  ```bash
  python scripts/development/dev.py validate-title "<your-title>"
  ```
- **Allowed Formats:**
  - `feat(core): add topological cycle detection`
  - `docs(backend): document API contracts`
  - `fix(security): sanitize connector error output`

---

## 3. Diagnostic Commands Summary

| Task | Diagnostic Command |
|---|---|
| **Full Health Check** | `python scripts/development/dev.py all` |
| **All Test Tracebacks** | `python -m unittest discover tests/ -v` |
| **TypeScript Errors** | `npx -p typescript tsc --noEmit` |
| **Doc Links Check** | `python scripts/ci/validate_docs.py` |
| **Language Navigation Check** | `python scripts/docs/generate_language_navigation.py --check` |
| **I18n Manifest Parity** | `python scripts/ci/validate_i18n.py` |

---

## 4. Related Documentation

- [Getting Started Guide](GETTING_STARTED.md)
- [Commands Reference](COMMANDS.md)
- [Testing Architecture](TESTING.md)
- [Contribution Workflow](CONTRIBUTION_WORKFLOW.md)
