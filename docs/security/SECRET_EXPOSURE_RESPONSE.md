# DERA Secret Exposure & Incident Response Playbook

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Security Contact:** `krishanth.b.2008@gmail.com`  
> **Classification:** Internal & Contributor Operational Security Playbook  

---

## 1. Cardinal Security Principle

> **Deleting a secret from Git history or making a repository private does NOT remediate a leak.**  
> Any credential, token, key, or connection string pushed to a public or shared repository must be treated as **immediately and permanently compromised**.

The primary remediation action is **instant revocation and rotation at the identity provider or database server**, followed by Git history sanitization.

---

## 2. Six-Phase Incident Response Lifecycle

```mermaid
flowchart TD
    LEAK[Secret Exposure Detected] --> P1[Phase 1: Immediate Revocation & Containment]
    P1 --> P2[Phase 2: Credential Re-issuance & Rotation]
    P2 --> P3[Phase 3: Impact Assessment & Access Log Audit]
    P3 --> P4[Phase 4: Git History Sanitization]
    P4 --> P5[Phase 5: Post-Mortem & Incident Report]
    P5 --> P6[Phase 6: Preventative Engineering Hardening]
```

### Phase 1: Immediate Revocation & Containment (T+0 to T+30 Minutes)
1. **Revoke the Credential:** Immediately log into the affected service (PostgreSQL database, cloud console, GitHub, NPM) and revoke or invalidate the leaked secret.
2. **Terminate Active Sessions:** For database users, terminate all active connection sessions associated with the compromised role:
   ```sql
   -- PostgreSQL example
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = 'compromised_user';
   ALTER ROLE compromised_user NOLOGIN;
   ```
3. **Do Not Panic-Edit Git:** Avoid pushing quick "delete secret" commits before revocation, as public commit scrapers cache historical commits within seconds of ingestion.

### Phase 2: Credential Re-issuance & Rotation (T+30 to T+60 Minutes)
1. Provision a new credential following DERA least-privilege principles (read-only catalog access, complex random password >= 32 chars).
2. Update local `.env` or staging environment configurations using secure injection channels.
3. Verify connectivity with the rotated credentials.

### Phase 3: Impact Assessment & Log Audit (T+1 to T+4 Hours)
1. Query authentication and audit logs for the compromised credential from the moment the commit was pushed until the revocation timestamp.
2. Inspect for unauthorized queries, data access, schema modifications, or privilege escalations.
3. If customer or tenant data was exposed, initiate legal and regulatory breach notification procedures in accordance with applicable data protection laws.

### Phase 4: Git History Sanitization (T+4 to T+12 Hours)
1. Use [`git-filter-repo`](https://github.com/newren/git-filter-repo) (recommended by Git core) to rewrite repository history:
   ```bash
   git filter-repo --replace-text expressions.txt
   ```
2. Coordinate with maintainers to force-push the sanitized history to remote tracking branches.
3. In GitHub Settings, contact GitHub Support if public caching or cached view URLs retain the leaked commit object.

### Phase 5: Post-Mortem & Incident Documentation (Within 48 Hours)
1. Document the incident timeline, root cause, exposed assets, log inspection findings, and remediation actions.
2. Store the post-mortem report privately unless public disclosure is required by governance guidelines.
3. Never include the real plaintext secret in tickets, commit messages, or post-mortem summaries.

### Phase 6: Preventative Engineering Hardening (Ongoing)
1. **Pre-Commit Verification:** Run automated secret scanners (`gitleaks`, `trufflehog`) locally or via pre-commit hooks.
2. **Exclusion Hardening:** Ensure [`.dockerignore`](../../.dockerignore) and [`.gitignore`](../../.gitignore) explicitly block:
   * `.env`, `.env.*`, `*.env`
   * `*.pem`, `*.key`, `*.p12`, `*.pfx`
   * `credentials.json`, `service-account*.json`
   * `id_rsa`, `id_ed25519`
3. **Dummy Mock Values:** For tests and documentation fixtures, strictly use recognizable mock credentials:
   ```python
   # Safe test fixture pattern
   TEST_CONNECTION = "sqlite:///:memory:"
   MOCK_PG_DSN = "postgresql://dera_mock:test_password_fixture@127.0.0.1:5432/mock_db"
   ```

---

## 3. Contact & Reporting Escalation

To report suspected credential leaks in DERA repositories:
* Direct maintainer contact: **Bunga Krishanth** (`krishanth.b.2008@gmail.com`)
* GitHub Security Advisory: **[Report Leak Privately](https://github.com/krishanth7/dera/security/advisories/new)**
