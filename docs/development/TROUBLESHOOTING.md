# DERA Development Troubleshooting & FAQ

> **Phase:** 1.2 Monorepo Architecture Foundation  
> **Status:** Active Knowledge Base  

---

## 1. Common Issues & Solutions

### Issue 1: `ModuleNotFoundError: No module named 'dera_core'` or `'dera_connectors'`
- **Cause:** Python test discovery was run without packages installed in editable mode or without `tests/__init__.py` bootstrapping.
- **Resolution:**
  - Install dependencies in editable mode: `pip install -e ".[dev]"`
  - Or run tests using the cross-platform runner: `python scripts/development/dev.py test`
  - Or ensure `tests/__init__.py` is present in your branch (auto-bootstraps `sys.path`).

### Issue 2: `error TS2591: Cannot find name 'process'` during `tsc`
- **Cause:** TypeScript strict mode checking Node environment variables in browser-facing code without `@types/node`.
- **Resolution:** In `apps/web/src/lib/api-client.ts`, use safe ambient declaration:
  ```ts
  declare const process: { env?: Record<string, string | undefined> } | undefined;
  ```

### Issue 3: PowerShell Script Execution Policy Error (`Activate.ps1 cannot be loaded`)
- **Cause:** Windows PowerShell default execution policy blocks unsigned local scripts.
- **Resolution:** Enable local script execution in current PowerShell session:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
  .venv\Scripts\Activate.ps1
  ```

### Issue 4: FastAPI Optional Dependency Skip
- **Symptom:** `Ran 17 tests ... OK (skipped=2)`
- **Cause:** `apps/api/src/dera_api/main.py` requires `fastapi` and `httpx` to run live HTTP integration tests. If not installed in your local Python environment, tests are safely skipped via `@unittest.skipUnless(FASTAPI_AVAILABLE)`.
- **Resolution:** Install dev extras: `pip install -e ".[dev]" fastapi httpx`.

### Issue 5: Port 8000 Conflict
- **Cause:** Another local service or previous uvicorn process is listening on port 8000.
- **Resolution:** Change port in `.env` (`DERA_API_PORT=8080`) or pass port to runner:
  ```bash
  python -m uvicorn dera_api.main:app --port 8080
  ```
