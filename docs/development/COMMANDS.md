# DERA Development Commands Reference

> **Phase:** 1.2 Monorepo Architecture Foundation  
> **Status:** Official Developer Command Catalog  

---

## 1. Unified Cross-Platform CLI (`dev.py`)

DERA provides a dedicated cross-platform runner (`scripts/development/dev.py`) that operates consistently on Windows PowerShell/cmd, Linux, and macOS:

| Command | Purpose | Underlying Subcommands |
|---|---|---|
| `python scripts/development/dev.py test` | Run all test suites | `python -m unittest discover tests/` |
| `python scripts/development/dev.py typecheck` | Run static TypeScript compiler typecheck | `npx -p typescript tsc --noEmit` |
| `python scripts/development/dev.py compile` | Byte-compile all Python packages | `python -m compileall packages/ apps/ tests/` |
| `python scripts/development/dev.py validate-docs` | Validate documentation markdown links and i18n parity | `scripts/ci/validate_docs.py` & `validate_i18n.py` |
| `python scripts/development/dev.py all` | Execute full baseline verification suite | Runs compile, tests, typecheck, and doc validation sequentially |

---

## 2. Standard `Makefile` Commands (UNIX / macOS)

For contributors using Linux or macOS with GNU Make installed:

| Target | Description | Example |
|---|---|---|
| `make help` | Print summary of all Makefile targets | `make help` |
| `make install` | Install Python dev extras and Node workspaces | `make install` |
| `make lint` | Run Ruff linter and documentation link checkers | `make lint` |
| `make format` | Auto-format Python source with Ruff | `make format` |
| `make typecheck` | Execute TypeScript compiler check | `make typecheck` |
| `make test` | Run Python unit, integration, and architecture tests | `make test` |
| `make build` | Compile Python packages and build Node workspaces | `make build` |
| `make dev-api` | Launch FastAPI gateway server with reload | `make dev-api` |
| `make clean` | Remove `__pycache__`, `.pytest_cache`, `.ruff_cache`, and build directories | `make clean` |

---

## 3. Direct Native Commands

Contributors who prefer running native commands directly can use:

### Python Commands
```bash
# Run unit & architecture tests
python -m unittest discover tests/

# Compile Python code
python -m compileall packages/ apps/ tests/

# Run API gateway locally
python -m uvicorn dera_api.main:app --reload --port 8000
```

### Node.js / TypeScript Commands
```bash
# Typecheck all TypeScript workspaces
npx -p typescript tsc --noEmit

# Run web studio development server (when web dependencies installed)
npm run --workspace=@dera/web dev
```
