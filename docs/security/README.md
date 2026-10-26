# DERA Security Architecture & Policies

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Security Contact:** `krishanth.b.2008@gmail.com`  
**Reporting URL:** [https://github.com/krishanth7/dera/security/advisories/new](https://github.com/krishanth7/dera/security/advisories/new)  
**License:** [MIT License](../../LICENSE)  

---

## 1. Overview

Because **DERA** connects directly to enterprise databases to reverse-engineer schemas, discover relationships, and visualize topologies, security and database integrity are paramount architectural concerns.

DERA enforces a **defense-in-depth security model** built on:
- Least-privilege, read-only metadata catalog access.
- Static SQL mutation interception.
- Zero customer row-data extraction.
- AES-256-GCM credential encryption at rest.
- Strictly deterministic, non-AI execution with zero cloud inference transmission.

```mermaid
flowchart TD
    SEC[DERA Security Architecture]
    POLICY[Root Security Policy: SECURITY.md]
    DB_SEC[Database Security & Access]
    DEV_SEC[Secure Development Standards]
    RESP[Vulnerability Response Workflow]
    THREAT[Threat Model Matrix]

    SEC --> POLICY
    SEC --> DB_SEC
    SEC --> DEV_SEC
    SEC --> RESP
    SEC --> THREAT
```

---

## 2. Security Documentation Index

| Document | Scope & Focus | Key Principles |
|---|---|---|
| [**SECURITY.md**](../../SECURITY.md) | Official project security policy & disclosure rules | Supported versions table, GitHub private advisory reporting, CVSS severity ratings, responsible disclosure. |
| [**DATABASE_SECURITY.md**](DATABASE_SECURITY.md) | Database connection & catalog access standards | Why `READ ONLY` transactions alone are insufficient, database role provisioning, credential lifecycle, query safety. |
| [**SECURE_DEVELOPMENT.md**](SECURE_DEVELOPMENT.md) | Secure development lifecycle & coding standards | Pydantic input validation, SQL parameterization, sanitized error handling, DevSecOps CI gates (Bandit, CodeQL). |
| [**VULNERABILITY_RESPONSE.md**](VULNERABILITY_RESPONSE.md) | Operational incident response workflow | 5-stage triage workflow, CVSS scoring guidelines, private security forks, coordinated disclosure timelines. |
| [**model.md**](model.md) | Architectural threat modeling matrix | Threat categories, potential attack vectors, mitigation mechanisms, SSRF prevention. |

---

## 3. Reporting a Vulnerability

If you discover a security vulnerability in DERA, please disclose it responsibly via GitHub Private Vulnerability Reporting:
👉 **[Report a Security Vulnerability](https://github.com/krishanth7/dera/security/advisories/new)**

Alternatively, email the maintainer directly at `krishanth.b.2008@gmail.com`.
