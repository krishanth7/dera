# DERA Diagnostics — Security & Safety Model

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Module:** `packages/core/src/dera/diagnostics/`  
**Status:** Canonical Reference  

---

## 1. Core Security Guarantees

1. **Read-Only Invariant:**
   - The diagnostic engine never executes SQL mutations, DDL scripts, or write operations on customer databases.
   - All evaluation operates solely in memory over canonical metadata models and immutable snapshots.
2. **Zero-AI Guarantee:**
   - Strict prohibition of AI, LLM, or external machine learning APIs.
   - Findings and recommendations are derived entirely from deterministic code logic and verifiable evidence.
3. **Data Protection & Sanitization:**
   - Embedded database credentials (passwords, connection strings, auth tokens) in evidence contexts are automatically scrubbed via `sanitize_value`.
   - Customer row data is never ingested, analyzed, or cached.
4. **Denial-of-Service Defense:**
   - Strict resource limits (`DiagnosticResourceLimits`) terminate runaways attempting to allocate unbounded objects, edges, or findings.
5. **Tenant Isolation:**
   - All REST API endpoints enforce workspace authorization via `resolve_authorized_workspace_id`.
   - Schemas and diagnostic reports are strictly isolated by workspace ID.
