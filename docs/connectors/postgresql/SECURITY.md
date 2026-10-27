# PostgreSQL Connector Security Model

## Multi-Layer Defense-in-Depth

The connector enforces security across five distinct layers:

```text
Layer 1: Protocol API Boundary
   └── Protocol exposes strictly read-only inspection methods.
       No execute_sql(), execute_ddl(), or mutation APIs exist.

Layer 2: SQL Validation & Parameterization
   └── Introspection executes only predefined pg_catalog queries.
       No customer table row queries. Identifiers safely parameterized.

Layer 3: Session-Level Hardening
   └── Every session executes:
       SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;
       SET statement_timeout = <ms>;

Layer 4: Network & SSRF Defenses
   └── Pre-flight target check blocks AWS/GCP/Azure link-local endpoints
       (169.254.169.254) and loopback addresses by default.

Layer 5: Database Least-Privilege Role
   └── Guidance specifies read grants only on system catalogs;
       no INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, or TRUNCATE.
```

---

## Secret & Credential Handling

- Passwords are typed as `pydantic.SecretStr` to prevent accidental inclusion in logs, traces, or string conversions.
- Diagnostic dictionaries pass through `sanitize_diagnostics()`, masking passwords and connection string secrets.
- Error messages pass through `mask_sensitive_strings()` to eliminate credential leakage from driver or server error traces.
- Credential references can resolve server-side via external secret vaults without transmitting raw secrets through client request payloads.
