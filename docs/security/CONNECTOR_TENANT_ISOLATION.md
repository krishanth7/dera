# Multi-Tenant Workspace Isolation

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Multi-Tenant Architecture & Boundaries

DERA is a multi-tenant platform where organizations operate within isolated **Workspaces**. A fundamental security guarantee is that tenant boundaries must never be breached:
- Workspace A cannot view, inspect, or execute queries against Workspace B's database connections.
- Cached metadata reports and schema snapshots are partitioned strictly by `workspace_id`.
- SQLite database files and storage roots are isolated by workspace subdirectories.
- Stable object identifiers (`ObjectId`) cryptographically bind the owning `workspace_id` into the digest.

---

## 2. Pre-Execution Workspace Validation

Tenant authorization is enforced in [`dera_connectors.security.authorization`](../../packages/connectors/src/dera_connectors/security/authorization.py):

```python
from dera_connectors.security import validate_workspace_authorization, TenantIsolationViolationError

try:
    # Verifies caller's workspace context matches resource workspace context
    validate_workspace_authorization(
        caller_workspace_id=caller_ctx.workspace_id,
        target_workspace_id=connection_config.workspace_id,
    )
except TenantIsolationViolationError as exc:
    # Raised BEFORE any secret resolution or network contact
    log_security_audit_event(...)
    raise
```

If the caller's workspace does not match the target workspace, the request is denied immediately with `TenantIsolationViolationError`. Database secrets are never resolved and network sockets are never opened for unauthorized callers.

---

## 3. Cryptographic Workspace Binding in Object Identity

In Phase 5.5, the stable object identity algorithm incorporates the `workspace_id` into the pre-digest framing:

```text
v1|<len_ws>:<workspace_id>|<len_conn>:<connection_id>|<len_engine>:<engine>|...
```

This guarantees that two workspaces introspecting identical databases (e.g. standard PostgreSQL `postgres` with default tables) generate distinct, non-overlapping `ObjectId` values, preventing cross-tenant collision and cache poisoning.
