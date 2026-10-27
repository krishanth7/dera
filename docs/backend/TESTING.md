# DERA Backend Testing & Quality Assurance Guide

> **Component:** `tests/unit`, `tests/integration`, `tests/architecture`  
> **Phase:** 4.1 — Python/FastAPI Application Foundation  
> **Status:** Authoritative Testing Protocol  

---

## 1. Testing Strategy & Principles

DERA enforces deterministic, isolated testing across all layers:

1. **Zero External Network Calls:** No tests make external HTTP requests or depend on cloud services.
2. **Deterministic Lifecycle:** Application instances are built using `create_app()` with isolated test settings.
3. **Lifespan Verification:** Tests use `TestClient(app)` context managers to execute startup and shutdown hooks cleanly.
4. **Defensive Error Coverage:** Tests verify that raw tracebacks and credentials are never leaked.

---

## 2. Test Suite Architecture

```text
tests/
├── architecture/
│   └── test_module_boundaries.py  # Enforces zero-AI & clean layer dependencies
├── integration/
│   ├── test_api_integration.py    # End-to-end HTTP endpoint & middleware tests
│   └── test_sqlite_connector.py   # Database connector read-only boundary tests
└── unit/
    ├── test_api.py                # Legacy API contract tests
    ├── test_api_config.py         # ApiSettings validation & profile tests
    ├── test_api_exceptions.py     # Exception handler & sanitization tests
    ├── test_api_factory.py        # create_app factory & OpenAPI tests
    └── test_api_lifecycle.py      # Lifespan startup/shutdown & readiness tests
```

---

## 3. Running Backend Tests

Run all unit, integration, and architecture tests with the built-in telemetry reporter:

```bash
python scripts/ci/test_reporter.py --test-dir tests/
```

### Running Specific Test Modules

```bash
# Configuration Unit Tests
python -m unittest tests/unit/test_api_config.py

# Application Factory Tests
python -m unittest tests/unit/test_api_factory.py

# Lifespan and Readiness Tests
python -m unittest tests/unit/test_api_lifecycle.py

# Exception Handling & Sanitization Tests
python -m unittest tests/unit/test_api_exceptions.py

# End-to-End API Integration Tests
python -m unittest tests/integration/test_api_integration.py
```

---

## 4. CI Integration

Backend test execution is automated via `.github/workflows/ci.yml`:

- **Matrix:** Python 3.12 and Python 3.13 on `ubuntu-latest`.
- **Static Analysis:** Ruff linting, formatting verification, and Bandit SAST.
- **Bytecode Verification:** `python -m compileall`.
- **Reporting:** JUnit XML (`reports/test-results.xml`) and JSON summary (`reports/test-summary.json`).
