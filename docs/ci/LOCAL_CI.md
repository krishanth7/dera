# DERA Local CI Reproduction Guide
**Database Engineering & Reverse Analysis**
*Understand Every Schema. Engineer Every Change.*

---

## 1. Overview

Every check performed in DERA's authoritative CI pipeline can be reproduced locally on Windows, Linux, or macOS. Contributors should run the relevant local verification commands before opening a pull request to ensure immediate qualification success.

---

## 2. One-Command Master Verification

For contributors modifying both Python backend and TypeScript frontend code, the DERA development CLI runs all primary verification suites in sequence:

```bash
# Run the complete local qualification baseline
python scripts/development/dev.py all
```

This single command deterministically executes:
1. Python Ruff linting (`ruff check`)
2. Python Ruff formatting check (`ruff format --check`)
3. Python bytecode compilation (`compileall`)
4. Bandit static application security scan (`bandit`)
5. Full Python test discovery (`unittest discover tests/`)
6. TypeScript static typechecking (`tsc --noEmit`)
7. Full documentation validation (`markdownlint-cli2`, link check, mermaid check, i18n check)

---

## 3. Targeted Local Reproduction by Domain

### 3.1 Python Backend Checks
If your changes touch `packages/core/`, `packages/connectors/`, `apps/api/`, or `tests/`:

```bash
# 1. Install dependencies in editable mode
pip install -e .

# 2. Run Ruff linting and import checks
python -m ruff check packages/ apps/ tests/ scripts/

# 3. Verify code formatting
python -m ruff format --check packages/ apps/ tests/ scripts/

# To automatically reformat files with Ruff:
python -m ruff format packages/ apps/ tests/ scripts/

# 4. Check bytecode compilation
python -m compileall packages/ apps/ tests/ scripts/

# 5. Run static security testing (Bandit)
python -m bandit -r packages/core/src/ apps/api/src/ -ll -q

# 6. Execute the full Python test suite
python -m unittest discover tests/

# 7. Validate package build integrity (sdist & wheel)
python -m build --sdist --wheel
```

---

### 3.2 Frontend & TypeScript Workspace Checks
If your changes touch `apps/web/`, `packages/contracts/`, or `package.json`:

```bash
# 1. Install Node dependencies
npm ci

# 2. Run TypeScript static typecheck
npm run typecheck

# 3. Build all workspace packages (@dera/contracts and @dera/web)
npm run build
```

---

### 3.3 Architecture & Module Boundary Checks
If your changes modify package structure, dependencies, or connector queries:

```bash
# Verify zero-AI policies, unidirectional dependency flow, and read-only boundaries
python -m unittest tests/architecture/test_module_boundaries.py
```

---

### 3.4 Database Connector Integration Tests
Integration tests run against synthetic, non-production test databases:

#### SQLite Integration (Zero External Services Needed)
```bash
# Runs in-memory and temporary SQLite database tests
python -m unittest tests/integration/test_sqlite_connector.py
```

#### PostgreSQL Service Container (Optional Local Docker Check)
If you have Docker installed and want to run an ephemeral PostgreSQL 16 container matching CI:

```bash
# 1. Launch disposable PostgreSQL 16 container
docker run -d --name dera-test-pg -e POSTGRES_DB=dera_test_db -e POSTGRES_USER=dera_test_user -e POSTGRES_PASSWORD=dera_ephemeral_test_password -p 5432:5432 postgres:16-alpine

# 2. Verify container readiness
docker exec dera-test-pg pg_isready

# 3. Cleanup container after testing
docker rm -f dera-test-pg
```

---

### 3.5 Documentation-Only Changes
If you are only contributing documentation or internationalization translations (`docs/**/*.md` or `README.md`), you do **not** need to install Python backend dependencies or build wheels:

```bash
# Run full hermetic documentation quality verification
npm run docs:check
```

This runs:
- `npm run docs:lint`: Markdownlint rule conformance
- `python scripts/ci/validate_docs.py`: Internal links, anchors, and file references
- `python scripts/ci/validate_mermaid.py`: Mermaid diagram syntax and direction
- `python scripts/docs/generate_language_navigation.py --check`: 10-language navigation parity
- `python scripts/ci/validate_i18n.py`: Canonical language manifest validation

---

### 3.6 Pull Request Governance Checks
Before opening or updating a pull request:

```bash
# Validate Conventional Commit format on your commit/PR title
python scripts/development/dev.py validate-title "feat(connectors): add PostgreSQL catalog inspection"
```
