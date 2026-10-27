# Connector Security Audit Logging

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Audit Logging Principles

Security audit logging provides an immutable, auditable trail of all security-sensitive connector actions:
- Connection requests and egress validation outcomes.
- Query allowlist checks and lexical analysis results.
- Read-only violation attempts.
- SSRF blocks and forbidden destination attempts.
- Cross-workspace isolation denials.
- Deadline expirations and user-initiated cancellations.

All audit events are recorded in structured JSON format and subjected to mandatory credential redaction before logging.

---

## 2. Security Audit Event Schema

Audit events are defined in [`dera_connectors.security.audit`](../../packages/connectors/src/dera_connectors/security/audit.py):

| Field | Type | Description |
| :--- | :--- | :--- |
| **`event_id`** | `str` (hex UUID) | Unique identifier for the audit event. |
| **`timestamp_utc`** | `str` (ISO 8601) | Accurate UTC timestamp when evaluation occurred. |
| **`workspace_id`** | `str` | Authenticated tenant workspace context. |
| **`user_id`** | `str \| None` | User identifier initiating the operation. |
| **`engine`** | `str` | Database engine (`postgresql`, `sqlite`, `mysql`, `mariadb`). |
| **`operation_id`** | `str` | Unique operation ID (e.g. `postgres.catalog.tables`). |
| **`status`** | `str` | `ALLOW`, `DENY`, `VIOLATION`, `TIMEOUT`, `CANCELLED`. |
| **`duration_ms`** | `float` | Duration of the security evaluation in milliseconds. |
| **`details`** | `dict[str, Any]` | Sanitized diagnostic context (credentials scrubbed). |

---

## 3. Usage Example

```python
from dera_connectors.security import log_security_audit_event

event = log_security_audit_event(
    workspace_id="9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    engine="postgresql",
    operation_id="postgres.catalog.tables",
    status="ALLOW",
    duration_ms=2.4,
    details={"schema": "public", "host": "db.prod.internal"},
)
```

Structured logger output:
```text
SECURITY_AUDIT: [64dbd4251be3] op=postgres.catalog.tables engine=postgresql workspace=9b1deb4d status=ALLOW duration=2.40ms
```
