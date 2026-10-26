# Getting Started with DERA Development

> **Audience:** Core contributors, external developers, and platform engineers  
> **Supported Platforms:** Windows 10/11, Linux (Ubuntu/Debian, Fedora, Arch), macOS  
> **Maintainer:** Krishanth  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Prerequisites

Before setting up DERA locally, ensure your workstation has the following runtimes installed:

| Tool | Minimum Version | Recommended Version | Verification Command | Platform Status |
|---|---|---|---|---|
| **Python** | `3.12+` | `3.12` or `3.13` | `python --version` | **Verified on Windows & Linux** |
| **Node.js** | `20.x LTS` | `20.x` or `22.x LTS` | `node --version` | **Verified on Windows & Linux** |
| **npm** | `10.x` | Latest | `npm --version` | **Verified on Windows & Linux** |
| **Git** | `2.40+` | Latest | `git --version` | **Verified on Windows & Linux** |

---

## 2. Step-by-Step Setup Guide

### Step 1: Clone the Repository
```bash
git clone https://github.com/krishanth7/dera.git
cd dera
```

### Step 2: Set Up Python Virtual Environment
We strongly recommend using a dedicated virtual environment:

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

> **Windows PowerShell Execution Policy Note:** If activating `.venv\Scripts\Activate.ps1` produces an execution policy error, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```

### Step 3: Install Node.js Workspaces
Install root and subpackage dependencies using npm:
```bash
npm install
```

### Step 4: Configure Local Environment Variables
Create a local `.env` configuration file from the sanitized template:

**On Linux / macOS:**
```bash
cp .env.example .env
```

**On Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

---

## 3. Verifying Your Local Setup

Execute the unified cross-platform baseline verification suite:

```bash
# Using the cross-platform runner (Windows / macOS / Linux)
python scripts/development/dev.py all
```

### Expected Output
When execution completes successfully, the runner outputs:
```text
Listing 'packages/'...
Listing 'apps/'...
Listing 'tests/'...
Ran 47 tests in 0.58s
OK (skipped=2)
Validating 78+ markdown documentation files...
SUCCESS: All markdown documentation files are valid.
SUCCESS: All 12 documents have verified, synchronized navigation.
[SUCCESS]: All development baseline checks passed successfully.
```

---

## 4. Running Local Development Services

### 4.1 Starting the FastAPI Backend Gateway
Launch the local API server on `127.0.0.1:8000`:
```bash
python -m uvicorn dera_api.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI Raw JSON Schema: `http://127.0.0.1:8000/openapi.json`
- Health Telemetry Endpoint: `http://127.0.0.1:8000/health`
- Platform Meta Endpoint: `http://127.0.0.1:8000/api/v1/meta`

### 4.2 Starting the Next.js Web Studio
Launch the web frontend development server on `http://127.0.0.1:3000`:
```bash
npm run --workspace=@dera/web dev
```
- Visual Studio Dashboard: `http://127.0.0.1:3000`

---

## 5. Running Focused Verification Suites

| Target Test Suite | Command | Purpose |
|---|---|---|
| **All Automated Tests** | `python scripts/development/dev.py test` | Runs all 47 unit, integration, and architecture tests |
| **Unit Tests Only** | `python -m unittest discover tests/unit` | Tests domain models, Kahn's algorithm, and diagnostics |
| **Integration Tests** | `python -m unittest discover tests/integration` | Tests SQLite catalog extraction against live databases |
| **Architecture Boundaries** | `python -m unittest tests/architecture/test_module_boundaries.py` | Asserts Zero-AI imports, core independence, and read-only query checks |
| **Regression Tests** | `python -m unittest discover tests/regression` | Verifies SHA-256 schema hashing invariants |
| **Language Navigation** | `python -m unittest discover tests/docs` | Validates 10-language navigation banner parity |
| **TypeScript Compilation** | `npx -p typescript tsc --noEmit` | Strict compile-time typecheck across all TypeScript workspaces |
| **Documentation Links** | `python scripts/ci/validate_docs.py` | Validates internal markdown links and H1 heading hierarchy |

---

## 6. Troubleshooting Common Onboarding Issues

- **`ModuleNotFoundError: No module named 'dera'` or `'dera_core'`:**  
  Run `pip install -e ".[dev]"` from the repository root, or ensure tests are launched via `python scripts/development/dev.py test`.
- **Port 8000 Conflict:**  
  Change the listening port via command-line: `python -m uvicorn dera_api.main:app --port 8080` or update `DERA_API_PORT` in your `.env`.
- **TypeScript Error `Cannot find module '@dera/contracts'`:**  
  Run `npm install` from the repository root so npm symlinks local workspaces.

For further assistance, consult [COMMANDS.md](COMMANDS.md), [TESTING.md](TESTING.md), or [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
