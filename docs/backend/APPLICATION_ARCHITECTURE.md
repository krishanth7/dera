# DERA Backend Application Architecture

> **Workspace:** `apps/api`  
> **Framework:** FastAPI / Python 3.12+  
> **Service Name:** DERA API Gateway (`dera-api`)  
> **Status:** Operational Scaffold (Implemented)  
> **Maintainer:** Krishanth  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Overview & Architectural Role

The **DERA API Gateway** (`apps/api`) is the HTTP service layer of the DERA platform. It acts as an asynchronous transport gateway between client applications (such as the `apps/web` studio or developer CLI tools) and DERA's lower-level deterministic core and connector packages.

The backend is deliberately designed as a **stateless, thin transport layer**:
- It validates incoming HTTP requests using Pydantic.
- It injects defensive security headers and manages CORS policies.
- It dispatches domain requests to `packages/core` and `packages/connectors`.
- It converts structured domain exceptions into standard HTTP error responses.
- It enforces strict non-AI execution and loopback binding defaults.

---

## 2. Directory Layout & Module Structure

```
apps/api/
├── pyproject.toml                     # Python package metadata and dependencies
└── src/
    └── dera_api/
        ├── __init__.py                # Package version declaration
        ├── main.py                    # Application entry point, middleware & route definitions
        ├── core/
        │   ├── config.py              # Immutable ApiSettings dataclass
        │   └── exceptions.py          # Structured HTTP exception formatting
        ├── middleware/
        │   └── security.py            # OWASP defensive headers middleware
        └── schemas/
            └── health.py              # Pydantic response models for health and meta
```

---

## 3. Application Entry Point & Configuration

### 3.1 Application Entry Point (`dera_api.main`)
The FastAPI application instance is instantiated in [`apps/api/src/dera_api/main.py`](../../apps/api/src/dera_api/main.py):

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import dera
from dera_api.core.config import get_settings
from dera_api.middleware.security import SecurityHeadersMiddleware

settings = get_settings()

app = FastAPI(
    title="DERA API",
    description="Deterministic Database Engineering & Reverse Analysis Platform API",
    version=dera.__version__,
)
```

### 3.2 Configuration Management (`dera_api.core.config`)
Configuration is managed via an immutable, frozen dataclass [`ApiSettings`](../../apps/api/src/dera_api/core/config.py) which reads from environment variables:

| Setting Field | Environment Variable | Default Value | Description |
|---|---|---|---|
| `app_name` | — | `"DERA API Gateway"` | Canonical application identifier |
| `version` | — | `"0.1.0-dev"` | API release specification version |
| `environment` | `DERA_ENV` | `"development"` | Active runtime environment |
| `api_prefix` | — | `"/api/v1"` | Base prefix for versioned endpoints |
| `host` | `DERA_API_HOST` | `"127.0.0.1"` | Loopback IP binding (prevents external exposure by default) |
| `port` | `DERA_API_PORT` | `8000` | HTTP listening port |
| `cors_origins` | `DERA_CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins list |
| `read_only_enforced`| — | `True` | Invariant enforcing read-only database access |
| `zero_ai_policy_enforced` | — | `True` | Invariant guaranteeing non-AI operation |

---

## 4. Middleware & Security Boundaries

### 4.1 Security Headers Middleware (`SecurityHeadersMiddleware`)
Adhering to OWASP defense-in-depth principles, [`SecurityHeadersMiddleware`](../../apps/api/src/dera_api/middleware/security.py) intercepts every incoming HTTP request and appends defensive response headers:

| Header Name | Value | Purpose |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Prevents browser MIME-type sniffing. |
| `X-Frame-Options` | `DENY` | Prevents clickjacking by forbidding embedding in iframes. |
| `X-XSS-Protection` | `1; mode=block` | Enables legacy browser cross-site scripting filter. |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Protects sensitive URL query parameters from leaking. |
| `X-DERA-Policy` | `DETERMINISTIC_ZERO_AI` | Explicit cryptographic header asserting non-AI processing. |

### 4.2 Cross-Origin Resource Sharing (CORS)
FastAPI's standard `CORSMiddleware` restricts browser cross-origin requests:
- Allowed Origins: Configurable via `DERA_CORS_ORIGINS` (defaults strictly to `http://localhost:3000`).
- Allowed Methods: `["GET", "POST", "OPTIONS"]` (mutating verbs `PUT`, `DELETE`, `PATCH` are disabled).
- Allow Credentials: `True`.

---

## 5. Exception Handling & Serialization

Domain errors originating from `packages/core` or `packages/connectors` inherit from `DeraError`. In [`apps/api/src/dera_api/core/exceptions.py`](../../apps/api/src/dera_api/core/exceptions.py), domain exceptions are formatted into consistent JSON error envelopes:

```json
{
  "success": false,
  "status_code": 409,
  "error": {
    "type": "CycleDetectedError",
    "message": "Circular foreign key dependency detected",
    "details": {
      "cycle_path": ["users", "orders", "users"]
    }
  }
}
```

---

## 6. Implemented Routes vs. Planned Extensions

### 6.1 Implemented Endpoints
1. `GET /health`: Health verification returning operational status, service name, and version.
2. `GET /info`: Official platform identity, maintainer attribution, and engineering philosophy.
3. `GET /api/v1/meta`: Extended platform capabilities, security flags, and supported database dialects.

For exact schema payloads and curl examples, see [API Contracts](API_CONTRACTS.md).

### 6.2 Planned Endpoints (Phase 5 & Beyond)
- `POST /api/v1/inspect`: Triggers catalog extraction against a target database and returns a canonical `SchemaSnapshot`.
- `POST /api/v1/diff`: Accepts two `SchemaSnapshot` payloads and computes structural AST diffs.
- `POST /api/v1/graph`: Computes topological sort and foreign-key dependency edges.

---

## 7. Local Development & Startup Commands

```bash
# Launch FastAPI development server with hot-reload on loopback 127.0.0.1:8000
python -m uvicorn dera_api.main:app --reload --host 127.0.0.1 --port 8000

# Access Swagger interactive UI
# http://127.0.0.1:8000/docs

# Access raw OpenAPI specification
# http://127.0.0.1:8000/openapi.json
```

---

## 8. Related Documentation

- [Backend Documentation Index](README.md)
- [API Contracts & Endpoint Specifications](API_CONTRACTS.md)
- [System Architecture Overview](../architecture/SYSTEM_OVERVIEW.md)
- [Module Boundaries](../architecture/MODULE_BOUNDARIES.md)
