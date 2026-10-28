# Phase 6.4 Dependency Analysis Security & Resource Protection

## 1. Zero Mutation & Passive Analysis

The dependency analysis engine complies with the strict DERA security standard:
- **No Database Mutation**: All analysis operations are 100% in-memory and passive. No DDL, DML, or SQL queries are executed against customer databases.
- **Disconnected Execution**: The engine operates purely on frozen metadata representations (`SchemaRepresentation` and `ForeignKeyGraph`). It requires zero live database network connections.

---

## 2. Resource Limits & Denial-of-Service Defense

Graph algorithms such as elementary cycle enumeration and transitive closures have exponential or polynomial worst-case complexity on adversarial graph topologies (e.g., complete directed graphs $K_n$).

DERA defends against algorithmic complexity attacks via `DependencyResourceLimits`:

| Resource Limit | Default | Purpose |
| :--- | :--- | :--- |
| `max_nodes` | 100,000 | Caps total tables analyzed to bound memory consumption. |
| `max_edges` | 500,000 | Caps total foreign key relationships analyzed. |
| `max_cycles` | 1,000 | Bounded cycle circuit breaker preventing exponential enumeration loops. |
| `max_recursion_depth` | 10,000 | Protects against call-stack exhaustion during deep DFS traversals. |
| `max_levels` | 10,000 | Protects against pathological deep chain recursion. |
| `max_serialized_bytes` | 10,000,000 | Bounded payload size for RFC 8785 JSON outputs. |

If any threshold is exceeded during analysis, the engine raises a `DependencyResourceLimitError` or cleanly truncates enumeration while recording audit findings.
