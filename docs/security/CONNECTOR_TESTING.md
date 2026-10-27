# Connector Security Testing & Verification Guide

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Security Testing Strategy

DERA's connector security qualification combines unit, negative adversarial, network boundary, filesystem containment, and cross-engine regression testing across six dedicated test suites:

```text
tests/
  ├── security/
  │     ├── connectors/
  │     │     ├── test_read_only_enforcement.py (DDL/DML mutations, comment stripping, dangerous functions)
  │     │     ├── test_query_allowlist.py (Operation registry, engine matching, parameter checks)
  │     │     ├── test_credential_handling.py (Encapsulation, repr safety, null byte rejection)
  │     │     └── test_resource_limits.py (Result row caps, identifier bounds, retry eligibility)
  │     ├── network/
  │     │     ├── test_ssrf_egress_protection.py (Cloud metadata, loopback, private CIDR, port blocks)
  │     │     └── test_dns_rebinding_defense.py (Destination IP pinning, multi-answer validation)
  │     ├── filesystem/
  │     │     └── test_sqlite_isolation.py (Root containment, symlink escapes, device files, read-only URIs)
  │     └── tenancy/
  │           └── test_workspace_isolation.py (Cross-workspace denials, pipeline execution order)
  ├── integration/
  │     └── connector_safety/
  │           ├── test_timeouts_and_cancellation.py (Central budgets, monotonic deadlines, cancellation propagation)
  │           └── test_audit_logging.py (Structured security event logging, redaction guarantees)
  └── regression/
        └── connectors/
              └── test_cross_engine_safety_regression.py (Cross-engine PostgreSQL, SQLite, MySQL, MariaDB validation)
```

---

## 2. Test Execution Commands

### Run All Security Test Suites

```bash
# Run all connector and platform security tests
python -m unittest discover tests/security

# Run integration safety tests
python -m unittest discover tests/integration/connector_safety

# Run cross-engine connector safety regression tests
python -m unittest discover tests/regression/connectors
```

### Run Entire Connector & Metadata Suite

```bash
python -m unittest discover tests/connectors
python -m unittest discover tests/metadata
```

---

## 3. Negative & Adversarial Test Coverage

| Test Area | Adversarial Vector Tested | Expected Result |
| :--- | :--- | :--- |
| **Read-Only** | `DROP`, `TRUNCATE`, `ALTER`, `CREATE`, `INSERT`, `UPDATE`, `DELETE` | `ReadOnlySecurityViolationError` raised; zero SQL dispatched. |
| **Lexical** | Comment wrappers: `/* comment */ DROP TABLE users;`, `--\nDELETE` | Comments stripped; mutation detected and blocked. |
| **Immunity** | Keywords in string literals: `WHERE status = 'drop'` | String literals replaced; valid introspection query permitted. |
| **Functions** | `pg_terminate_backend`, `xp_cmdshell`, `sys_eval` | Administrative function blocked with `ReadOnlySecurityViolationError`. |
| **File I/O** | `INTO OUTFILE`, `INTO DUMPFILE`, `COPY ... FROM` | File escape blocked with `ReadOnlySecurityViolationError`. |
| **SSRF** | `169.254.169.254`, `metadata.google.internal`, `instance-data` | Cloud metadata blocked with `SSRFSecurityViolationError`. |
| **Ports** | Targeting port 22 (SSH), 2375 (Docker), 10250 (Kubelet) | Administrative service port blocked with `SSRFSecurityViolationError`. |
| **DNS Rebinding** | Pre-flight resolved to 93.184.216.34, connection shifts to 169.254.169.254 | Destination drift blocked with `DNSRebindingViolationError`. |
| **Filesystem** | Traversal `../../etc/passwd` or outside approved root | Path traversal blocked with `FilesystemIsolationViolationError`. |
| **Devices** | Path named `CON.db`, `NUL.db`, `/dev/sda` | Device path blocked with `FilesystemIsolationViolationError`. |
| **Multi-Tenancy** | Caller in Workspace A accessing Connection in Workspace B | Cross-workspace access blocked with `TenantIsolationViolationError`. |
| **Timeouts** | Multi-step query inspection exceeding overall deadline | Inspection aborted with `TimeoutExceededViolationError`. |
| **Cancellation**| Caller cancels parent token during active sub-query | Operation interrupted with `CancellationRequestedViolationError`. |
