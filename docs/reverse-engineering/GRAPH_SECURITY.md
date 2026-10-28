# Graph Security Architecture & Controls

## 1. Zero Database Interaction Principle

The Foreign Key Graph engine operates exclusively on in-memory canonical schema representations and reconstructed structural metadata:

- **No SQL Execution**: The graph engine does not generate, parse, or execute SQL queries.
- **No Database Connections**: No socket, network, or filesystem connections are opened to customer databases.
- **No Mutation Interfaces**: There are no mutation APIs, update commands, or database modification routines.
- **Read-Only / Pure Computation**: Graph construction and traversal are purely deterministic in-memory operations.

---

## 2. Resource Limits & Denial-of-Service Defense

To prevent resource exhaustion (memory, CPU, or recursion depth) from maliciously crafted or pathologically large schemas, [`GraphResourceLimits`](file:///packages/core/src/dera/reverse_engineering/graph/limits.py) enforces strict boundaries:

```python
class GraphResourceLimits(BaseModel):
    max_nodes: int = 10_000
    max_edges: int = 50_000
    max_column_pairs: int = 100_000
    max_traversal_depth: int = 50
    max_visited_nodes: int = 10_000
    max_returned_edges: int = 50_000
    max_serialized_bytes: int = 10_000_000  # 10 MB
```

### Protection Mechanisms:
1. **Node & Edge Thresholds**: Exceeding node or edge count aborts construction with [`GraphResourceLimitError`](file:///packages/core/src/dera/reverse_engineering/graph/errors.py).
2. **Traversal Depth Limit**: Deeply nested or cyclical graphs are bounded at `max_traversal_depth=50` by default.
3. **Payload Truncation / Bounding**: Serialization and deserialization reject payloads larger than 10 MB.

---

## 3. Workspace Isolation & Multi-Tenancy

Every `TableNode`, `ForeignKeyEdge`, and `ForeignKeyGraph` is strictly bound to its canonical workspace scope:

- Cross-workspace edge injection is detected during validation (`WORKSPACE_ISOLATION` rule).
- Object IDs derived in Phase 5.5 embed workspace-specific length-prefixed SHA-256 prefixes, preventing accidental or intentional cross-tenant link forgery.

---

## 4. Metadata Sanitization

- **Untrusted Identifiers**: Constraint names, table names, and column names are treated as pure data literals and never evaluated as executable code or passed to shell/eval commands.
- **Forbidden Extra Fields**: All Pydantic models specify `extra="forbid"`, preventing prototype pollution or unknown attribute injection.
