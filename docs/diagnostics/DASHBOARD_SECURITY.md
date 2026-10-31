# Dashboard Security and Authorization Specification

## Security Architecture

The Diagnostics Dashboard implements defense-in-depth across frontend rendering, data transport, and API authorization.

## Security Controls

1. **Strict Multi-Tenant Isolation**: Evaluation requests require workspace authentication via JWT/session tokens; cross-tenant schema evaluation returns `403 Forbidden`.
2. **Untrusted Metadata Sanitization**: Schema table names, column names, and constraint expressions are treated as untrusted strings and sanitized against Cross-Site Scripting (XSS).
3. **Secret Scrubbing**: Database passwords, auth tokens, and connection strings are scrubbed before reaching frontend response models.
4. **Content Security Policy (CSP)**: Enforced via `next.config.ts`, disallowing `unsafe-eval` and restricting script/connect sources.
5. **Read-Only Enclosure**: The dashboard cannot mutate database catalog objects or execute DDL statements.
