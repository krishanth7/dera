# DERA Development Commands Reference

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Maintainer:** Krishanth  
> **Status:** Official Developer Command Catalog  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Unified Cross-Platform Runner (`scripts/development/dev.py`)

DERA provides a dedicated cross-platform command runner (`scripts/development/dev.py`) designed to operate identically on Windows PowerShell, macOS, and Linux without requiring GNU Make.

| Command | Purpose | Prerequisites | Exact Syntax | Expected Behavior | Exit Code | Troubleshooting |
|---|---|---|---|---|---|---|
| **Run All Baseline Checks** | Executes compile, tests, typecheck, and doc validation sequentially | Python 3.12+, Node 20+, npm packages installed | `python scripts/development/dev.py all` | Runs 5 checks in sequence and reports overall pass/fail status | `0` on success; `1` on failure | Run individual failing check to isolate the issue |
| **Run Test Suite** | Discovers and executes all 47 automated tests | Python 3.12+ | `python scripts/development/dev.py test` | Runs `unittest discover tests/` | `0` on pass; `1` on test failure | Inspect traceback for failing test assertion |
| **Run TypeScript Typecheck** | Compiles TypeScript workspaces without emitting files | Node.js 20+, `npx` | `python scripts/development/dev.py typecheck` | Executes `npx -p typescript tsc --noEmit` | `0` on pass; `1` on type error | Ensure `npm install` was run in repo root |
| **Byte-Compile Python** | Compiles all `.py` files to detect syntax errors | Python 3.12+ | `python scripts/development/dev.py compile` | Executes `compileall` on `packages/`, `apps/`, `tests/` | `0` on pass; `1` on syntax error | Check line indicated in syntax error |
| **Validate Documentation** | Validates internal markdown links and 10-language parity | Python 3.12+ | `python scripts/development/dev.py validate-docs` | Runs `validate_docs.py`, `generate_language_navigation.py --check`, `validate_i18n.py` | `0` on pass; `1` on broken link | Check path and anchor spelling in reported files |
| **Validate Commit/PR Title** | Asserts Conventional Commits format | Python 3.12+ | `python scripts/development/dev.py validate-title "<title>"` | Verifies type, scope, and description syntax | `0` on pass; `1` on invalid format | Ensure format matches `<type>(<scope>): <desc>` |
| **Install Git Hooks** | Installs local commit-msg hook | Git | `python scripts/development/dev.py install-hooks` | Writes executable `.git/hooks/commit-msg` | `0` on success | Check write permissions in `.git/hooks/` |

---

## 2. Native Direct Commands

Contributors who prefer executing native toolchain commands directly can use the following commands:

### 2.1 Python Dependency Installation & Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate on Linux/macOS
source .venv/bin/activate

# Activate on Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Install package in editable mode with development extras
pip install -e ".[dev]"
```

### 2.2 Running Python Tests
```bash
# Run all tests (unit, integration, architecture, regression, docs)
python -m unittest discover tests/

# Run unit tests only
python -m unittest discover tests/unit

# Run architecture boundary and non-AI enforcement tests
python -m unittest tests/architecture/test_module_boundaries.py

# Run SQLite connector integration tests
python -m unittest tests/integration/test_sqlite_connector.py

# Run SHA-256 schema hash regression tests
python -m unittest discover tests/regression

# Run 10-language navigation tests
python -m unittest discover tests/docs
```

### 2.3 Running the API Gateway
```bash
# Run FastAPI server with hot-reload on loopback 127.0.0.1:8000
python -m uvicorn dera_api.main:app --reload --host 127.0.0.1 --port 8000

# Run API server on custom port
python -m uvicorn dera_api.main:app --port 8080
```

### 2.4 Running the Web Frontend
```bash
# Install npm dependencies across workspaces
npm install

# Typecheck all TypeScript code
npx -p typescript tsc --noEmit

# Launch Next.js web studio in development mode
npm run --workspace=@dera/web dev

# Build production bundle for web studio
npm run --workspace=@dera/web build
```

### 2.5 Documentation & Internationalization Validation
```bash
# Validate internal markdown links and H1 heading hierarchy
python scripts/ci/validate_docs.py

# Check 10-language navigation synchronization across READMEs
python scripts/docs/generate_language_navigation.py --check

# Synchronize 10-language navigation banner across all target files
python scripts/docs/generate_language_navigation.py --write

# Validate international README translations and language manifest
python scripts/ci/validate_i18n.py
```

---

## 3. Standard `Makefile` Commands (UNIX / macOS)

For contributors working on Linux or macOS systems with GNU Make installed:

| Target | Underlying Command | Description |
|---|---|---|
| `make test` | `python -m unittest discover tests/` | Runs full Python test suite |
| `make typecheck` | `npx -p typescript tsc --noEmit` | Compiles TypeScript workspaces |
| `make build` | `python -m compileall packages/ apps/ tests/ && npm run --workspace=@dera/web build` | Compiles Python and builds web bundle |
| `make dev-api` | `python -m uvicorn dera_api.main:app --reload --port 8000` | Launches API development server |
| `make clean` | Removes `__pycache__`, `.pytest_cache`, build artifacts | Cleans temporary cache directories |

---

## 4. Related Documentation

- [Getting Started Guide](GETTING_STARTED.md)
- [Testing Architecture Guide](TESTING.md)
- [Development Troubleshooting](TROUBLESHOOTING.md)
- [Contribution Workflow](CONTRIBUTION_WORKFLOW.md)
