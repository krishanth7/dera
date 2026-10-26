# Getting Started with DERA Development

> **Audience:** Core contributors, external developers, and platform engineers  
> **Platforms Supported:** Windows 10/11, macOS, Linux (Ubuntu/Debian, Fedora, Arch)  

---

## 1. Prerequisites

Before setting up DERA locally, ensure your machine has the following runtimes installed:

| Tool | Minimum Version | Recommended Version | Verification Command |
|---|---|---|---|
| **Python** | `3.12+` | `3.12` or `3.13` | `python --version` |
| **Node.js** | `20.x LTS` | `20.x` or `22.x LTS` | `node --version` |
| **npm** | `10.x` | Latest | `npm --version` |
| **Git** | `2.40+` | Latest | `git --version` |

---

## 2. Step-by-Step Setup

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

### Step 3: Install Node.js Workspaces
Install root and subpackage dependencies using npm:
```bash
npm install
```

### Step 4: Configure Local Environment Variables
Copy the safe template into `.env`:
```bash
# On Linux/macOS
cp .env.example .env

# On Windows (PowerShell)
Copy-Item .env.example .env
```

---

## 3. Verifying Your Setup

Run the unified cross-platform verification suite:

```bash
# Using the cross-platform runner (Windows / macOS / Linux)
python scripts/development/dev.py all

# Alternatively using make (macOS / Linux)
make build test typecheck
```

### Expected Output
When execution completes successfully, the runner outputs:
```text
Listing 'packages/'...
Listing 'apps/'...
Listing 'tests/'...
Ran 32 tests in 0.25s
OK (skipped=2)
Validating 69 markdown documentation files...
SUCCESS: All 69 markdown documentation files are valid.
Validating 10 multilingual documentation files in i18n...
SUCCESS: All 10 language documentation files verified with valid navigation and parity.
[SUCCESS]: All development baseline checks passed successfully.
```

---

## 4. Running the Local Applications

DERA separates its presentation, API gateway, and reverse-engineering engines into decoupled workspaces:

### Starting the FastAPI Backend Gateway
```bash
# Run the local API server on http://127.0.0.1:8000
python -m uvicorn dera_api.main:app --reload --port 8000
```
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- Health Telemetry Endpoint: `http://127.0.0.1:8000/health`

### Starting the Next.js Web Studio (Development Mode)
```bash
# Run the web frontend on http://127.0.0.1:3000
npm run dev --workspace=apps/web
```
- Visual Studio Canvas: `http://127.0.0.1:3000`

---

## 5. Running Focused Tests

| Target Test Suite | Command |
|---|---|
| **All Automated Tests** | `python scripts/development/dev.py test` |
| **Unit Tests Only** | `python -m unittest discover tests/unit` |
| **Integration Tests (SQLite & PostgreSQL)** | `python -m unittest discover tests/integration` |
| **Regression Tests (DAG & Hash Invariants)** | `python -m unittest discover tests/regression` |
| **Architecture Boundaries Test** | `python -m unittest tests/architecture/test_boundaries.py` |
| **TypeScript Strict Compilation** | `python scripts/development/dev.py typecheck` |

---

## 6. Troubleshooting Common Issues

- **PowerShell Script Execution Policy on Windows:**
  If activating `.venv\Scripts\Activate.ps1` gives an execution policy error, run:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- **Port 8000 Already in Use:**
  Specify an alternative port for Uvicorn:
  ```bash
  python -m uvicorn dera_api.main:app --reload --port 8080
  ```
- **Documentation Link Failures:**
  Run the automated documentation linter to identify broken references:
  ```bash
  python scripts/ci/validate_docs.py
  ```

For additional assistance, consult [COMMANDS.md](COMMANDS.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md), or our [Discussions Forum](https://github.com/krishanth7/dera/discussions).
