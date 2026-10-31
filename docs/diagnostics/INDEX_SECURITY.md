# Security Architecture for Index and Constraint Diagnostics

## 1. Guarantees & Constraints
1. **Strictly Read-Only**: Analysis evaluates canonical metadata models and immutable snapshots in memory. No network connections are initiated to source databases during diagnostic evaluation.
2. **Zero SQL Execution**: No DDL (`CREATE INDEX`, `DROP INDEX`, `ALTER TABLE`) or DML is ever generated or executed against any customer database.
3. **Passive Check Expression Handling**: Check constraint expressions are treated as untrusted, tainted text. They are never parsed with arbitrary SQL execution or evaluated as code.
4. **Credential Isolation**: Database passwords, session tokens, and connection strings are excluded from diagnostic contexts and redacted from evidence payloads.
5. **Multi-Tenant Authorization**: All diagnostic requests verify tenant and workspace boundaries, preventing cross-tenant leakage of schemas, findings, or reports.
