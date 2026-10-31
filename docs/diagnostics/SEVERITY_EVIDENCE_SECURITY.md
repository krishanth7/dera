# Diagnostic Security and Authorization Specification

## Overview

DERA Phase 8.5 enforces strict security policies across all diagnostic evaluation, severity determination, suppression governance, and recommendation reporting.

## Core Security Invariants

1. **Read-Only Operation**: The diagnostic subsystem is strictly read-only. It never executes DDL or DML mutations against source customer databases.
2. **AI/LLM/ML Prohibition**: Recommendations, severities, and finding summaries are generated purely through deterministic static rules and peer-reviewed templates. Third-party generative AI and external cloud LLM APIs are strictly prohibited.
3. **Workspace Isolation (Multi-Tenancy)**: Diagnostic reports, suppression records, and severity overrides are strictly partitioned by `workspace_id` and `snapshot_id`. Cross-tenant querying is rejected at the API middleware layer.
4. **Secret Minimization**: Evidence collection scrubs sensitive credentials (passwords, auth tokens, database connection strings) from evidence payloads.
5. **Role-Based Authorization**:
   - Creating or revoking suppressions requires explicit workspace administrative role (`admin` or `lead_engineer`).
   - Overriding effective severity requires administrative privilege and logs the authorized actor identity.
6. **Resource Bounds**: Evaluations limit maximum findings (default 10,000) and evidence items per finding (default 100) to protect against denial-of-service on extreme schemas.
