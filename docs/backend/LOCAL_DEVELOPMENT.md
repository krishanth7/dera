# DERA Backend Local Development Guide

> **Component:** `apps/api/src/dera_api`  
> **Phase:** 4.1 — Python/FastAPI Application Foundation  
> **Status:** Active Developer Guide  

---

## 1. Prerequisites

- Python 3.12 or Python 3.13
- Node.js 20+ (for full monorepo scripts & TypeScript verification)
- Git

---

## 2. Environment Setup

Clone the repository and install editable dependencies from the monorepo root:

```bash
# Clone repository
git clone https://github.com/krishanth7/dera.git
cd dera

# Install monorepo in editable mode with development dependencies
pip install -e .
pip install pydantic pydantic-settings networkx sqlglot fastapi uvicorn httpx ruff bandit
```

### Environment Configuration File

Copy the template configuration file:

```bash
cp apps/api/.env.example apps/api/.env
```

Review default settings in `apps/api/.env`. In local development, the server binds to `127.0.0.1:8000` with debug features enabled.

---

## 3. Starting the Backend Server

### Development Mode (with Live Reload)

```bash
python -m uvicorn dera_api.main:app --host 127.0.0.1 --port 8000 --reload
```

Alternatively, invoke `main.py` directly:

```bash
python apps/api/src/dera_api/main.py
```

### Production-Mode Simulation (No Reload)

```bash
python -m uvicorn dera_api.main:app --host 127.0.0.1 --port 8000 --workers 1 --log-level info
```

---

## 4. Verifying Endpoints

Once the server is running, verify basic connectivity:

```bash
# Process Liveness Probe
curl -i http://127.0.0.1:8000/health/live

# Application Readiness Probe
curl -i http://127.0.0.1:8000/health/ready

# Platform Capabilities & Non-AI Policy
curl -i http://127.0.0.1:8000/api/v1/meta

# Fast Heartbeat Ping
curl -i http://127.0.0.1:8000/api/v1/ping
```

### Interactive API Documentation

When `docs_enabled` is active (default in development and testing):

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- OpenAPI Specification: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 5. Local Quality Assurance Commands

Run the full local verification pipeline before submitting any changes:

```bash
# 1. Run Unit & Integration Tests with Telemetry
python scripts/ci/test_reporter.py --test-dir tests/

# 2. Run Ruff Linting & Code Formatting Checks
python -m ruff check packages/ apps/ tests/ scripts/
python -m ruff format --check packages/ apps/ tests/ scripts/

# 3. Compile Python Bytecode
python -m compileall packages/ apps/ tests/ scripts/

# 4. Run Static Security Analysis (Bandit)
python -m bandit -r packages/core/src/ apps/api/src/ -ll -q

# 5. Validate Documentation & Multilingual Navigation
npm run docs:check
```
