# Cooperative Connector Cancellation

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Cooperative Cancellation Architecture

In long-running or distributed database operations, a user or client may cancel an inspection job at any time. When cancellation is signaled:
1. Active database driver queries must be interrupted immediately (e.g. via `asyncpg` connection closing or PyMySQL query aborts).
2. Unfinished transactions must be rolled back.
3. Leaked connection handles must be returned to the pool or closed.
4. Downstream processing (e.g. normalization, reverse engineering) must be skipped.

DERA coordinates this via [`EnhancedCancellationToken`](../../packages/connectors/src/dera_connectors/security/cancellation.py).

---

## 2. Parent-Child Cancellation Hierarchy

Cancellation tokens support hierarchical composition:

```text
+-------------------------------------------------------+
|  Job-Level Parent Token (Triggered by REST API or UI)  |
+-------------------------------------------------------+
                           |
                           v (Inherited)
+-------------------------------------------------------+
|       Connector Context Child Token (Per Adapter)     |
+-------------------------------------------------------+
                           |
                           v (Inherited)
+-------------------------------------------------------+
|       Sub-Query Execution Token (Per Catalog Query)   |
+-------------------------------------------------------+
```

When a parent token is cancelled via `token.cancel("User aborted inspection")`, all registered child tokens and asynchronous callbacks are immediately executed.

---

## 3. Implementation Example

```python
from dera_connectors.security import EnhancedCancellationToken, CancellationRequestedViolationError

parent_token = EnhancedCancellationToken()
child_token = parent_token.create_child()

# Register resource cleanup callback
child_token.register_callback(lambda: print("Cleaning up active socket resources..."))

# Cancel from parent
parent_token.cancel("Inspection aborted by administrator")

# Checking in active loop
try:
    child_token.raise_if_cancelled()
except CancellationRequestedViolationError as exc:
    print(f"Aborted: {exc}")
```
