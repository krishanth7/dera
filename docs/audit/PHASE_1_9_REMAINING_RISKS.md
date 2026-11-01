# Phase 1–9 Residual Risk Register & Operational Guidance
**Document ID:** `DERA-AUDIT-REMAINING-RISKS`  
**Date:** 2026-11-01  
**Status:** **LOW RESIDUAL RISK (Non-Blocking)**  

---

## 1. Risk Assessment Summary

Following the completion of P0 security remediation, durable relational persistence engineering, and comprehensive multi-instance verification, all critical and high-severity production blockers have been resolved.

The remaining risks identified below represent non-blocking operational considerations and future scalability enhancements.

---

## 2. Risk Register

| Risk ID | Title | Severity | Impact | Mitigation / Operational Recommendation | Blocker Status |
|:---|:---|:---:|:---|:---|:---:|
| **RSK-01** | Ultra-Large Schema Graph Memory Overhead | LOW | Schemas with >10,000 tables may require significant memory during in-process Tarjan cycle detection | Deploy background job worker (`dera-worker`) with dedicated memory allocation (2GB+) for extreme schemas | **NON-BLOCKING** |
| **RSK-02** | External Audit Ledger Anchoring | LOW | Cryptographic SHA-256 hash chains are tamper-evident within the relational DB but lack external hardware HSM/WORM anchoring | Integrate external RFC 3161 timestamping authority or cloud KMS digital signature service in future phases | **NON-BLOCKING** |
| **RSK-03** | Long-Running Network Introspection | LOW | Complex enterprise networks with multi-hop firewalls may encounter slow socket connects | Tuned `statement_timeout` and `connect_timeout` configured on all database connectors | **NON-BLOCKING** |
| **RSK-04** | Client Cookie Expiration Handling | LOW | Browser sessions idle beyond configured session lifetime require re-login | Standard HTTP 401 redirect handled gracefully by Next.js auth context | **NON-BLOCKING** |

---

## 3. Operational Deployment Guidance

1. **Database Migration Execution:**
   - Execute Alembic migration revision 005 prior to launching new API containers:
     ```bash
     alembic upgrade head
     ```
2. **Environment Variable Configuration:**
   - Ensure `DERA_ENVIRONMENT=production` to enforce strict SSRF loopback blocking.
   - Configure `DERA_SESSION_COOKIE_SECURE=true` for HTTPS production environments.
3. **Horizontal Scaling:**
   - Deploy multiple stateless API workers behind an application load balancer; all migration state is reliably coordinated via PostgreSQL.
