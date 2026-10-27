# Security Controls & Workspace Isolation (Phase 6.1)

## 1. Threat Model & Security Posture

The Phase 6.1 Schema Representation Layer operates on database metadata. Its threat boundaries are:
1. **Untrusted Metadata Inputs**: Malicious identifiers, pathological schemas, recursive structures, or excessive object counts attempting Denial-of-Service.
2. **Cross-Tenant Information Leakage**: Colliding object identifiers across distinct workspaces or customer tenants.
3. **Arbitrary Code Execution**: Injected code inside view definitions, trigger bodies, or CHECK constraints.
4. **Credential Exposure**: Accidental leakage of database passwords, tokens, or connection strings in serialized schema representations.

---

## 2. Implemented Security Controls

### 1. Cross-Workspace Isolation
Canonical `ObjectId`s incorporate `workspace_id` in their length-prefixed SHA-256 frame:
```
FRAME = "v1|" + len(engine) + ":" + engine + "|" + len(workspace_id) + ":" + workspace_id + ...
```
Two tenants inspecting an identical schema (e.g. `public.users`) produce distinct `ObjectId`s, completely preventing cross-tenant collisions or state bleed in multi-tenant environments.

### 2. Zero Database Execution & No Reconnection
The schema representation layer:
- **Never connects to databases**: It operates entirely in memory on validated metadata.
- **Never executes SQL**: View definitions, check constraints, and trigger statements are stored as immutable text strings. They are never parsed with `eval` or executed against any database engine.

### 3. Resource Bounds & DoS Prevention
`SchemaResourceLimits` enforces hard caps on schema size:
- `max_total_objects` (default: 100,000) prevents memory exhaustion.
- `max_identifier_length` (default: 256) rejects buffer-overflow and long-string DoS attacks.
- `max_definition_bytes` (default: 1 MB) bounds view and trigger definitions.
- `max_references` (default: 50,000) limits reference graphs.

### 4. Malicious Identifier Protection
Identifiers containing SQL injection sequences (e.g. `users'; DROP TABLE users; --`) are treated strictly as string data literals. Length bounds are enforced and no SQL parser is invoked.

### 5. Credential Sanitization
All serialized schemas, provenance models, and error messages are strictly free of connection strings, passwords, or auth tokens.
