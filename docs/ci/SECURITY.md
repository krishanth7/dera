# DERA CI/CD Security Architecture & Policy

Security is a primary engineering discipline for DERA. This document outlines the security controls, permission boundaries, and supply chain integrity mechanisms governing our automated workflows.

---

## 1. Threat Modeling & Core Security Principles

### Principle 1: Least Privilege by Default
All GitHub Actions workflows define explicit top-level `permissions:` blocks restricting token capabilities to the minimum necessary:
* Standard verification workflows default to `contents: read`.
* Workflows without repository access requirements specify `permissions: {}` (e.g., PR title validation).
* Security scanning requires scoped `security-events: write` (`codeql.yml`).
* Tagged releases require `contents: write` (`release.yml`).

### Principle 2: Safe Untrusted PR Boundaries
* DERA strictly avoids `pull_request_target` triggers whenever workflow steps execute code from the submitted pull request.
* All forks and external contributions run via `pull_request`, ensuring:
  * GitHub repository secrets are not exposed to forked workflows.
  * Tokens issued are strictly read-only.
  * Shell scripts cannot execute malicious instructions with repository write privileges.

### Principle 3: Safe Shell Injection Defenses
Untrusted event payloads (e.g., `github.event.pull_request.title`, `github.event.pull_request.body`) are **never** interpolated directly into bash or sh commands using `${{ ... }}`. Instead, they are passed as safely quoted environment variables:
```yaml
# SAFE:
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: python scripts/ci/validate_pr_title.py

# FORBIDDEN (Vulnerable to command injection):
run: echo "${{ github.event.pull_request.title }}"
```

### Principle 4: Zero Production Database Access
* DERA reverse engineers database metadata, not production data.
* Workflows never access live corporate networks, production VPCs, or cloud-hosted database clusters.
* All integration tests run against ephemeral containers (`postgres:16-alpine`) or in-memory SQLite instances (`:memory:`) created on the runner and destroyed immediately upon job completion.

### Principle 5: Deterministic Analysis Without AI
* In adherence to DERA's founding philosophy, our CI pipelines do not transmit schema metadata, code diffs, or diagnostic outputs to external generative AI services or third-party inference APIs.

---

## 2. Token Permission Matrix

| Workflow | `contents` | `pull-requests` | `security-events` | `actions` | Rationale |
|---|---|---|---|---|---|
| `ci.yml` | `read` | None | None | None | Source checkout, test execution, database integration |
| `codeql.yml` | `read` | None | `write` | `read` | SAST SARIF upload to Security Tab |
| `pr-title.yml` | `read` | None | None | None | PR title format verification |
| `pr-readiness.yml` | `read` | None | None | None | Description checklist audit |
| `documentation.yml` | `read` | None | None | None | Read documentation files |
| `i18n.yml` | `read` | None | None | None | Read multilingual markdown docs |
| `dependency-review.yml` | `read` | `read` | None | None | Audit PR dependency diffs |
| `security-tests.yml` | `read` | None | None | None | Static security linting |
| `schema-regression.yml` | `read` | None | None | None | Execute regression fixtures |
| `sqlite-compatibility.yml`| `read` | None | None | None | Execute SQLite matrix |
| `docker.yml` | `read` | None | None | None | Validate Dockerfile syntax |
| `mutation.yml` | `read` | None | None | None | Run mutation verification |
| `release.yml` | `write` | None | None | None | Create GitHub Release and assets |
| `release-recovery.yml` | `read` | None | None | None | Audit published release assets |
| `ci-performance.yml` | `read` | None | None | `read` | Query run timing telemetry |
| `cache-maintenance.yml` | `read` | None | None | `read` | Query cache list metadata |

---

## 3. Reporting Vulnerabilities

For security disclosures or vulnerabilities identified in DERA workflows or codebase, consult [SECURITY.md](../../SECURITY.md) for encrypted reporting instructions.
