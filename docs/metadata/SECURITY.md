# Metadata Normalization Security & Boundaries

**Subsystem:** `dera.metadata.validation`  

---

## 1. Security Invariants

The normalization layer operates under strict security boundaries:
1. **Zero Database Connections:** Operates solely on already-inspected, serialized metadata models. Never opens sockets, pools, or connections.
2. **Zero SQL Execution:** Never evaluates, executes, or parses view definitions, trigger bodies, or check constraint expressions.
3. **Multi-Tenant Isolation:** ObjectIds incorporate `workspace_id` and `connection_id` when present, preventing cross-tenant identity collision.
4. **Credential Sanitation:** No credentials, tokens, or plaintext secrets are ingested or stored in canonical metadata.

---

## 2. Resource Boundaries

To prevent memory exhaustion or denial-of-service via adversarial database schemas, the normalizer strictly enforces:

| Resource Boundary | Configured Limit | Violation Exception |
| :--- | :--- | :--- |
| **Max Identifier Length** | 1,024 characters | `MetadataLimitExceededError` |
| **Max Definition Size** | 1,048,576 bytes (1 MB) | `MetadataLimitExceededError` |
| **Max Total Objects** | 100,000 objects per database | `MetadataLimitExceededError` |
