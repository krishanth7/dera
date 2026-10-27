# DERA Backend Configuration Reference

> **Component:** `apps/api/src/dera_api/core/config.py`  
> **Phase:** 4.1 — Python/FastAPI Application Foundation  
> **Status:** Authoritative Configuration Reference  

---

## 1. Overview

Application configuration is managed by `dera_api.core.config.ApiSettings` using Pydantic v2 and `pydantic-settings`. Settings can be specified via environment variables, `.env` files, or injected directly during application factory instantiation.

---

## 2. Configuration Variables Matrix

| Variable | Alias | Default | Type | Description |
|---|---|---|---|---|
| `APP_NAME` | `DERA_APP_NAME` | `"DERA API Gateway"` | `str` | Display name of the service |
| `APP_VERSION` | `DERA_VERSION` | Dynamic (`0.1.0-dev`) | `str` | Semantic platform version |
| `APP_ENV` | `DERA_ENV` | `"development"` | `str` | Environment profile (`development`, `testing`, `production`) |
| `APP_DEBUG` | `DERA_DEBUG` | `false` | `bool` | Enable debug mode (strictly forbidden in production) |
| `APP_HOST` | `DERA_API_HOST` | `"127.0.0.1"` | `str` | Bind network interface address |
| `APP_PORT` | `DERA_API_PORT` | `8000` | `int` | Network listening port (1–65535) |
| `APP_LOG_LEVEL` | `DERA_LOG_LEVEL` | `"INFO"` | `str` | Verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `APP_API_PREFIX` | `DERA_API_PREFIX` | `"/api/v1"` | `str` | Versioned route namespace root |
| `APP_CORS_ORIGINS` | `DERA_CORS_ORIGINS` | `["http://localhost:3000", "http://127.0.0.1:3000"]` | `list[str]` | Allowed CORS origins (comma-separated or list) |
| `APP_DOCS_ENABLED` | `DERA_DOCS_ENABLED` | Dynamic | `bool` | Enables OpenAPI endpoints (`/docs`, `/redoc`, `/openapi.json`) |
| `APP_REQUEST_ID_HEADER` | `DERA_REQUEST_ID_HEADER` | `"X-Request-ID"` | `str` | HTTP header name for request correlation |
| `READ_ONLY_ENFORCED` | `DERA_READ_ONLY_ENFORCED` | `true` | `bool` | Enforces read-only DB connector boundary |
| `ZERO_AI_POLICY_ENFORCED` | `DERA_ZERO_AI_POLICY_ENFORCED` | `true` | `bool` | Deterministic zero-AI architectural guarantee |

---

## 3. Environment Profiles

DERA supports three validated environment profiles:

### `development`

- **Purpose:** Local workstation development.
- **Defaults:** `docs_enabled=True`, `debug=False` (can be toggled).
- **CORS:** Allows `http://localhost:3000` and loopback addresses.

### `testing`

- **Purpose:** Automated test execution (unit, integration, CI).
- **Defaults:** Isolated memory settings, deterministic test client instantiation.
- **CORS:** Controlled test origin allowlists.

### `production`

- **Purpose:** Secure production deployment.
- **Strict Enforcement Rules:**
  - `debug=True` raises a fatal validation error on startup.
  - Wildcard CORS origins (`"*"`) raise a fatal validation error on startup.
  - `docs_enabled` defaults to `False` unless explicitly overridden.
  - Request logging redacts all tokens, passwords, and connection strings.

---

## 4. Precedence & Dependency Injection

Configuration settings resolve in the following order of precedence:

1. **Explicit Injected Settings:** Passed directly to `create_app(settings=...)`.
2. **Environment Variables:** Set in the host environment or container runtime.
3. **Dotenv File:** Values defined in `apps/api/.env`.
4. **Field Defaults:** Built-in default values in `ApiSettings`.

To access settings within request endpoints, use FastAPI's dependency injection:

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from dera_api.core.config import ApiSettings
from dera_api.dependencies.common import get_app_settings

router = APIRouter()

@router.get("/custom-endpoint")
def custom_endpoint(
    settings: Annotated[ApiSettings, Depends(get_app_settings)],
):
    return {"environment": settings.environment}
```
