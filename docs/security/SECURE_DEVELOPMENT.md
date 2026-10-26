# Secure Development Policy & Engineering Standards

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Policy Status:** Active Engineering Standard  
**Maintainer:** [Krishanth](https://github.com/krishanth7)  
**Parent Policy:** [SECURITY.md](../../SECURITY.md)  
**License:** [MIT License](../../LICENSE)  

---

## 1. Overview & Objectives

DERA's Secure Development Lifecycle (SDLC) establishes technical requirements and review practices to prevent security vulnerabilities from entering the codebase.

Because DERA handles sensitive database metadata and network connections, every contributor and maintainer must adhere to these secure development standards.

Our engineering standards align with industry best practices, including the **OWASP Top 10**, **OWASP ASVS (Application Security Verification Standard)**, and **CWE (Common Weakness Enumeration)** guidelines.

---

## 2. Secure Coding Standards

### 2.1 Input Validation & Type Safety (OWASP A03: Injection)
- **Strict Schema Validation:** All external inputs entering the application (via HTTP requests, CLI arguments, or configuration files) must be validated using strict schemas:
  - **Python / Backend (`apps/api`):** Use Pydantic v2 models (`pydantic>=2.0.0`) with explicit type definitions, regex constraints, and bounds checking.
  - **TypeScript / Frontend (`apps/web`):** Use strict typing and runtime contract validators.
- **Reject Unexpected Input:** Input validation must follow allow-list validation rather than block-lists.
- **SQL Identifier Validation:** Database object names must match strict alphanumeric patterns (`^[a-zA-Z_][a-zA-Z0-9_]*$`).

### 2.2 Output Encoding & Injection Prevention (CWE-79, CWE-89)
- **HTML / UI Encoding:** React's built-in JSX rendering automatically escapes untrusted text. Dangerous attributes such as `dangerouslySetInnerHTML` are strictly prohibited unless sanitized via DOMPurify with maintainer sign-off.
- **SQL Parameterization:** Queries to databases must use parameterized bindings (`$1`, `?`) rather than raw string concatenation or f-strings.

### 2.3 Authentication & Session Management (OWASP A07: Identification and Authentication Failures)
- **Token Security:** Bearer tokens used for API authorization must use cryptographically secure random generators (`secrets.token_urlsafe(32)`).
- **Session Expiration:** API sessions must enforce idle and absolute timeouts.
- **Credential Storage:** User passwords (where user accounts are implemented) must be hashed using modern adaptive hashing algorithms (**Argon2id** or **bcrypt** with appropriate work factors). Never use MD5, SHA-1, or unsalted SHA-256.

### 2.4 Authorization & Multi-Tenant Isolation (OWASP A01: Broken Access Control)
- **Server-Side Authorization:** Access control must be validated on the server for every single API request. Never rely on client-side routing guards alone.
- **Tenant Key Scoping:** In multi-tenant environments, every database query and metadata artifact must include the `tenant_id` or `organization_id` in its lookup filter to prevent cross-tenant information disclosure.

### 2.5 Error Handling & Exception Sanitization (OWASP A05: Security Misconfiguration)
- **No Stack Traces in Production:** Detailed tracebacks, internal file paths, and database query texts must never be returned in HTTP error responses to clients.
- **Generic Client Responses:** Clients receive clean, structured error responses (`{"error": "ResourceNotFound", "message": "The requested resource was not found"}`). Full diagnostic traces must be logged internally to secure log streams.

### 2.6 Secrets Handling & Prevention (CWE-798: Hardcoded Credentials)
- **Zero Secrets in Repository:** Passwords, API keys, private keys, and encryption secrets must never be committed to Git.
- **Automated Pre-Commit Checks:** All contributors are encouraged to install pre-commit hooks (`.pre-commit-config.yaml`) to block accidental credential commits.
- **Environment Isolation:** Secrets are provided exclusively via environment variables or secret vaults.

### 2.7 Logging & Auditability (OWASP A09: Security Logging and Monitoring Failures)
- **Sanitized Structured Logging:** All log output must be structured JSON.
- **Masking Sensitive Data:** The logging layer must automatically mask:
  - Database connection passwords (`postgres://user:***@host/db`)
  - Authorization headers (`Bearer ***`)
  - Cryptographic keys and session tokens
- **Security Audit Events:** Authentication failures, permission denials, and connection attempts must be recorded with timestamp, client IP, and user identity.

### 2.8 Secure Defaults & Loopback Binding
- **Development Server Binding:** Local development servers (Uvicorn, FastAPI, Vite/Next.js) must explicitly bind to loopback (`127.0.0.1`) by default, never `0.0.0.0`, to prevent exposing development servers on local networks.

---

## 3. Supply Chain & Dependency Hygiene

1. **Permissive Licensing:** All dependencies must comply with the [Third-Party License Policy](../governance/THIRD_PARTY_LICENSES.md).
2. **Pinned Versions:** Dependency manifests must specify explicit version ranges to prevent unexpected upstream breaking changes or dependency hijacking.
3. **Automated Dependabot Alerts:** Dependencies are monitored continuously for known CVEs via [`.github/dependabot.yml`](../../.github/dependabot.yml).
4. **Vulnerability Remediation:** High and critical severity dependency alerts must be triaged within 7 calendar days of notification.

---

## 4. Automated Security Testing (CI Gates)

Every pull request must pass the automated DevSecOps qualification pipeline defined in [`.github/workflows/security-tests.yml`](../../.github/workflows/security-tests.yml) and [`.github/workflows/codeql.yml`](../../.github/workflows/codeql.yml):

```mermaid
flowchart LR
    PR[Pull Request Submitted] --> SAST[Bandit Python SAST]
    PR --> CODEQL[GitHub CodeQL Analysis]
    PR --> LINT[Ruff & Typecheck]
    PR --> SEC_TESTS[Security Unit Tests]
    
    SAST --> GATE{All Clean?}
    CODEQL --> GATE
    LINT --> GATE
    SEC_TESTS --> GATE

    GATE -->|Pass: Zero High/Crit Warnings| APPROVE[Ready for Review]
    GATE -->|Fail: Vulnerability Flagged| BLOCK[Blocked from Merge]
```

- **Bandit SAST:** Scans all Python files for insecure functions, hardcoded binds, unsafe deserialization, and weak cryptography.
- **CodeQL Scanning:** Performs deep semantic taint analysis for injection vulnerabilities across the codebase.
- **Unit Security Tests:** Tests in `tests/unit/` verify loopback binding, error masking, and query mutation interception.

---

## 5. Security Code Review Checklist

Before approving any pull request, maintainers and reviewers must verify:
- [ ] Are all database operations strictly read-only?
- [ ] Is input validation enforced using Pydantic or strict typing?
- [ ] Are any SQL queries parameterized or safely escaped?
- [ ] Are error messages sanitized without leaking connection strings?
- [ ] Are any secrets, tokens, or credentials committed or logged?
- [ ] Does the change maintain the strictly deterministic, non-AI mandate?
- [ ] Do all automated security tests and CI gates pass with 100% green status?
