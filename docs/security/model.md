# DERA Security Model & Threat Mitigation

**Project:** DERA — Database Engineering & Reverse Analysis  
**Policy Reference:** [SECURITY.md](../../SECURITY.md)  
**License:** [MIT License](../../LICENSE)

---

## 1. Security Architecture Principles

DERA operates under a defense-in-depth security model designed specifically for database reverse engineering:

1. **Least Privilege by Default:** Database credentials supplied to DERA must only have read-only access to system metadata catalogs (`information_schema`, `pg_catalog`).
2. **Session-Level Read-Only Enforcement:** Connectors enforce transaction read-only modes before issuing queries:
   ```sql
   SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;
   ```
3. **Zero Customer Row Extraction:** Metadata inspection routines never issue `SELECT *` against application data tables. Only catalog definitions are inspected.
4. **Credential Isolation & Encryption:** Connection secrets are stored encrypted at rest using AES-256-GCM and decrypted in-memory only during active inspection tasks.
5. **SSRF Mitigation:** Target hostnames and IP addresses are validated against internal infrastructure blacklists and cloud metadata endpoints (`169.254.169.254`).
6. **Multi-Tenant Isolation:** All snapshots, diagrams, and logs are strictly scoped by tenant and organization IDs.

---

## 2. Threat Modeling Matrix

| Threat Category | Potential Attack Vector | DERA Defense Strategy |
|---|---|---|
| **Data Exfiltration** | Unauthorized extraction of sensitive records | Inspection queries exclusively target system catalog views |
| **Accidental Modification** | DDL/DML injection via user parameters | Enforced read-only transactions; parameterized catalog queries |
| **Credential Theft** | Interception of database passwords | AES-256-GCM encryption at rest; TLS 1.3 in transit; secret masking |
| **SSRF / Network Probing** | Submitting malicious internal URLs | Strict IP destination filtering; non-routable address blocking |
| **Cross-Tenant Access** | Accessing snapshots of other organizations | Role-based authorization; server-side tenant key verification |

---

## 3. Security Policies & Vulnerability Reporting

For detailed technical policies and operational procedures:
- [Root Security Policy](../../SECURITY.md)
- [Database Security & Access Policy](DATABASE_SECURITY.md)
- [Secure Development Standards](SECURE_DEVELOPMENT.md)
- [Vulnerability Response & Incident Disclosure](VULNERABILITY_RESPONSE.md)

Security vulnerabilities should be reported privately via:
- **GitHub Private Vulnerability Reporting:** [Report a Vulnerability](https://github.com/krishanth7/dera/security/advisories/new)
- **Security Contact:** `krishanth.b.2008@gmail.com`

