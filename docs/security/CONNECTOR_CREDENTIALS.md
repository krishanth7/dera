# Connector Credential Management & Masking

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Principles of Credential Confidentiality

Database connection strings, usernames, passwords, and private keys represent sensitive secrets. An accidental exposure in logs, telemetry, or error messages poses critical compromise risks to customer infrastructure.

DERA enforces three strict invariants:
1. **Zero Secret Persistence in Metadata:** Canonical metadata models, stable object IDs (`ObjectId`), and schema snapshots never contain plaintext passwords or connection URIs.
2. **Encapsulated Memory Representation:** Database credentials are encapsulated in [`DatabaseCredentials`](../../packages/connectors/src/dera_connectors/security/credentials.py) with `repr=False`, ensuring standard `str()` and `repr()` calls render `password='***'`.
3. **Deep Recursive Redaction:** All diagnostic dumps, error details, and log dictionaries pass through [`sanitize_diagnostics`](../../packages/connectors/src/dera_connectors/security/redaction.py).

---

## 2. Redaction Architecture

Credential masking is handled centrally in [`dera_connectors.security.redaction`](../../packages/connectors/src/dera_connectors/security/redaction.py):

```python
from dera_connectors.security import mask_sensitive_strings, sanitize_diagnostics

# Mask passwords embedded in connection strings
safe_uri = mask_sensitive_strings("postgresql://dbadmin:SuperSecret123@db.prod:5432/main")
# Result: 'postgresql://dbadmin:***@db.prod:5432/main'

# Recursively scrub diagnostics
raw_diag = {
    "host": "db.prod",
    "credentials": {
        "username": "dera_ro",
        "password": "Password123",
        "api_key": "live_key_998877",
    },
    "token": "top-secret",
}
safe_diag = sanitize_diagnostics(raw_diag)
```

The scrubber recursively inspects dictionary keys and list elements, masking any key matching forbidden substrings:
- `password`, `passwd`, `pwd`
- `secret`, `token`, `credential`, `auth_token`
- `private_key`, `api_key`, `apikey`, `bearer`
- `access_token`, `refresh_token`

---

## 3. Ephemeral Secret Resolution

Database secrets are decrypted or retrieved from platform secret storage only at connection time, immediately after workspace authorization has been confirmed. Plaintext passwords reside exclusively in transient local scopes and are cleared upon garbage collection or context teardown.
