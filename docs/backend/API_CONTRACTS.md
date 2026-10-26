# DERA Backend API Contracts & Reference

> **Service:** DERA API Gateway (`apps/api`)  
> **API Version:** `0.1.0-dev`  
> **Status:** Active & Verified  
> **Base URL:** `http://127.0.0.1:8000` (Default Loopback)  
> **OpenAPI Schema:** `http://127.0.0.1:8000/openapi.json`  
> **Interactive Docs:** `http://127.0.0.1:8000/docs`  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Overview & Protocol Guarantees

All endpoints exposed by the DERA API Gateway adhere to the following invariants:
1. **Zero AI Integration:** No endpoint invokes external inference APIs, language models, or probabilistic estimators.
2. **Deterministic Responses:** Responses for identical schema and platform queries are bit-for-bit identical.
3. **Security Headers:** Every HTTP response includes OWASP defensive headers (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, and `X-DERA-Policy: DETERMINISTIC_ZERO_AI`).
4. **Authentication:** In the current phase, endpoints are public metadata endpoints designed for local loopback development. Authentication and API keys are planned for multi-tenant production phases.

---

## 2. Implemented Endpoints Reference

### 2.1 Health Check Endpoint
- **HTTP Method:** `GET`
- **Route Path:** `/health`
- **Purpose:** Verifies service availability, process liveness, and release version.
- **Request Parameters:** None.
- **Request Body:** None.
- **Authentication:** None (Public).
- **Status Codes:**
  - `200 OK`: Service is operational.

#### Example Request
```bash
curl -s http://127.0.0.1:8000/health
```

#### Example Response
```json
{
  "status": "healthy",
  "service": "dera-api",
  "version": "0.1.0-dev"
}
```

---

### 2.2 Platform Information Endpoint
- **HTTP Method:** `GET`
- **Route Path:** `/info`
- **Purpose:** Exposes official platform identity, official tagline, maintainer attribution, and engineering philosophy.
- **Request Parameters:** None.
- **Request Body:** None.
- **Authentication:** None (Public).
- **Status Codes:**
  - `200 OK`: Platform information retrieved successfully.

#### Example Request
```bash
curl -s http://127.0.0.1:8000/info
```

#### Example Response
```json
{
  "project": "DERA",
  "name": "Database Engineering & Reverse Analysis",
  "tagline": "Understand Every Schema. Engineer Every Change.",
  "maintainer": "Krishanth",
  "philosophy": "Deterministic, non-AI database reverse engineering",
  "version": "0.1.0-dev"
}
```

---

### 2.3 Extended Platform Metadata Endpoint
- **HTTP Method:** `GET`
- **Route Path:** `/api/v1/meta`
- **Purpose:** Returns platform capabilities, runtime environment, security invariants, and supported database dialects.
- **Request Parameters:** None.
- **Request Body:** None.
- **Authentication:** None (Public).
- **Status Codes:**
  - `200 OK`: Metadata successfully retrieved.

#### Example Request
```bash
curl -s http://127.0.0.1:8000/api/v1/meta
```

#### Example Response
```json
{
  "name": "DERA API Gateway",
  "version": "0.1.0-dev",
  "environment": "development",
  "zero_ai_policy": true,
  "read_only_enforced": true,
  "supported_dialects": [
    "sqlite",
    "postgresql",
    "mysql",
    "mariadb"
  ]
}
```

---

## 3. Standard Error Envelope

When domain exceptions occur, error payloads adhere to the following schema defined in [`apps/api/src/dera_api/core/exceptions.py`](../../apps/api/src/dera_api/core/exceptions.py):

| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Always `false` on errors. |
| `status_code` | `integer` | HTTP status code (e.g. `400`, `403`, `404`, `409`, `500`). |
| `error.type` | `string` | Domain exception class name (e.g. `ReadOnlyViolationError`). |
| `error.message` | `string` | Human-readable explanation of the error. |
| `error.details` | `object` | Contextual dictionary (e.g. `cycle_path`, query snippets). |

#### Example Error Response (Cycle Detected)
```json
{
  "success": false,
  "status_code": 409,
  "error": {
    "type": "CycleDetectedError",
    "message": "Circular foreign key dependency detected",
    "details": {
      "cycle_path": [
        "public.orders",
        "public.invoices",
        "public.orders"
      ]
    }
  }
}
```

---

## 4. Planned Endpoints (Phase 5 & Future)

The following endpoints represent planned capabilities and are **not yet operational**:

| Method | Planned Path | Target Phase | Planned Purpose |
|---|---|---|---|
| `POST` | `/api/v1/inspect` | Phase 5 | Connects to a target database, extracts catalog metadata, and returns a `SchemaSnapshot`. |
| `POST` | `/api/v1/diff` | Phase 6 | Accepts two `SchemaSnapshot` payloads and calculates structural differences and migrations. |
| `POST` | `/api/v1/graph` | Phase 5 | Generates foreign-key topological order and cycle analysis for submitted tables. |
| `POST` | `/api/v1/diagnostics` | Phase 5 | Evaluates static anti-pattern rules against a submitted schema. |

---

## 5. Related Documentation

- [Backend Application Architecture](APPLICATION_ARCHITECTURE.md)
- [Backend Documentation Hub](README.md)
- [Shared Schema Contracts](../contracts/SCHEMA_CONTRACTS.md)
- [Database Connector Architecture](../connectors/CONNECTOR_ARCHITECTURE.md)
