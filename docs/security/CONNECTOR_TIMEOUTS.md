# Centralized Timeouts & Monotonic Deadlines

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Timeout Architecture & Policy

Database introspection workflows typically execute dozens of sequential catalog queries to retrieve schemas, tables, columns, constraints, foreign keys, indexes, views, and triggers. If each sub-query only resets an isolated query timeout, an inspection against a slow database could run indefinitely, exhausting server worker pools and memory.

DERA solves this by enforcing **monotonic deadline propagation**:
- A single overall inspection deadline (default 120.0s) is allocated at the start of the inspection.
- Sub-query timeouts are dynamically clamped to the remaining overall time via [`DeadlineTracker.allocate_sub_budget`](../../packages/connectors/src/dera_connectors/security/timeouts.py).
- Monotonic time (`time.monotonic()`) is used to ensure system clock adjustments do not skew timeout evaluation.

---

## 2. Centralized Timeout Budget

Configuration is managed by [`TimeoutBudget`](../../packages/connectors/src/dera_connectors/security/timeouts.py):

| Phase / Operation | Default Timeout | Min Allowed | Max Allowed | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Connection Setup** | 10.0s | 0.1s | 60.0s | TCP socket connection establishment. |
| **DNS Resolution** | 3.0s | 0.1s | 10.0s | Hostname lookup timeout. |
| **TLS Handshake** | 5.0s | 0.5s | 30.0s | TLS negotiation and certificate verification. |
| **Query Execution** | 30.0s | 0.1s | 180.0s | Individual catalog query statement timeout. |
| **Overall Inspection** | 120.0s | 1.0s | 600.0s | Full schema inspection budget across all queries. |
| **Metadata Normalization** | 15.0s | 0.5s | 60.0s | Canonical transformation and identity hashing. |
| **Connection Cleanup** | 5.0s | 0.5s | 15.0s | Clean pool disposal and session termination. |

---

## 3. Usage & Deadline Propagation

```python
from dera_connectors.security import DeadlineTracker, TimeoutExceededViolationError

tracker = DeadlineTracker(deadline_seconds=120.0, operation_name="full_schema_inspection")

for step in ["tables", "columns", "constraints", "indexes"]:
    tracker.check_deadline()
    step_timeout = tracker.allocate_sub_budget(proposed_seconds=30.0)
    # Execute query with step_timeout
```

If the remaining budget reaches zero, `tracker.check_deadline()` raises `TimeoutExceededViolationError` with details including elapsed and allocated durations.
