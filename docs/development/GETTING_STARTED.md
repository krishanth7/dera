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

If all checks exit with `[SUCCESS]`, your development environment is fully operational!
