# DERA Environment Configuration Guide

> **Phase:** 1.2 Monorepo Architecture Foundation  
> **Reference File:** [`.env.example`](../../.env.example)  

---

## 1. Environment Variable Architecture & Security

DERA separates environment variables into three strict tiers to prevent security risks:
1. **Server-Only Variables:** Consumed exclusively by `apps/api` and backend services. Never exposed to browser bundles.
2. **Public Frontend Variables (`NEXT_PUBLIC_*`):** Embedded into frontend code at build/runtime. Restricted exclusively to non-sensitive endpoints and UI feature flags.
3. **Local Test Target Databases:** Mock credentials used solely for local integration tests.

---

## 2. Variables Catalog

### Tier 1: API Gateway (Server-Only)

| Variable | Default Value | Description | Required in Production |
|---|---|---|---|
| `DERA_ENV` | `development` | Deployment environment (`development`, `staging`, `production`). | Yes |
| `DERA_API_HOST` | `0.0.0.0` | Host address to bind the API server. | Yes |
| `DERA_API_PORT` | `8000` | Port to listen for HTTP requests. | Yes |
| `DERA_API_LOG_LEVEL` | `info` | Logging verbosity (`debug`, `info`, `warning`, `error`). | No |
| `DERA_CORS_ORIGINS` | `http://localhost:3000` | Comma-separated list of allowed web origins for CORS headers. | Yes |
| `DERA_READ_ONLY_ENFORCED` | `true` | Enforces that all database connectors reject mutating queries. | **Mandatory True** |
| `DERA_ZERO_AI_ENFORCED` | `true` | Enforces non-AI deterministic execution mode. | **Mandatory True** |

### Tier 2: Web Studio (Public)

| Variable | Default Value | Description |
|---|---|---|
| `NEXT_PUBLIC_DERA_API_URL` | `http://localhost:8000` | Base URL of the backend API gateway. |
| `NEXT_PUBLIC_APP_ENV` | `development` | UI environment indicator. |
| `NEXT_PUBLIC_MAX_DIAGRAM_NODES` | `250` | Maximum number of entity nodes to render in ER diagrams before pagination. |

> [!CAUTION]
> **Zero Password Rule:** NEVER prefix database passwords, cloud tokens, or private secrets with `NEXT_PUBLIC_`. Any variable starting with `NEXT_PUBLIC_` is readable by any user in their browser!

### Tier 3: Local Test Databases (Local Testing Only)

| Variable | Default Value | Description |
|---|---|---|
| `DERA_TEST_SQLITE_PATH` | `:memory:` | SQLite path used for connector integration tests. |
| `DERA_TEST_POSTGRES_HOST` | `localhost` | Local ephemeral PostgreSQL test instance host. |
| `DERA_TEST_POSTGRES_PORT` | `5432` | Local PostgreSQL test instance port. |
| `DERA_TEST_POSTGRES_DB` | `dera_test` | Local PostgreSQL test database name. |
| `DERA_TEST_POSTGRES_USER` | `dera_tester` | Local PostgreSQL test database user. |
| `DERA_TEST_POSTGRES_PASSWORD` | `local_insecure_test_password` | Local test password (ephemeral container only). |
