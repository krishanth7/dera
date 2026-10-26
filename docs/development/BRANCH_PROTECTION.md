# DERA Branch Protection & Repository Rulesets

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Maintainer:** Krishanth ([@krishanth7](https://github.com/krishanth7))  
> **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
> **Target Branch:** `main`  

---

## 1. Overview & Policy Rationale

To maintain the production readiness, security, and deterministic integrity of DERA, the central `main` branch is strictly protected. Direct pushes and force pushes are blocked by automated GitHub branch rulesets.

This specification documents the required configuration for GitHub repository administrators.

---

## 2. Recommended Branch Protection Ruleset for `main`

The following settings should be configured in GitHub under **Repository Settings > Rules > Rulesets**:

### A. Target & Enforcement
- **Ruleset Name:** `main-branch-protection`
- **Enforcement Status:** Active
- **Target Branches:** Default branch (`main`)
- **Bypass List:** None (even repository administrators must adhere to pull request reviews and automated CI checks).

### B. Pull Request Requirements

| Setting | Recommended Value | Rationale |
|---|---|---|
| **Require a pull request before merging** | **Enabled** | Prevents direct commits to `main`. |
| **Required approving reviews** | **1** | At least one maintainer review is mandatory. |
| **Dismiss stale approvals when new commits are pushed** | **Enabled** | Ensures new modifications are re-verified. |
| **Require review from Code Owners** | **Enabled** | Enforces `.github/CODEOWNERS` authority. |
| **Require conversation resolution** | **Enabled** | All review comments must be addressed. |

### C. Required Status Checks (CI Gates)
All designated CI checks must pass before a pull request can be merged:

1. **`CI Gate`**: The top-level composite qualification workflow.
2. **`CodeQL Analysis (python)`**: Deep static semantic analysis for Python vulnerabilities.
3. **`CodeQL Analysis (javascript-typescript)`**: Deep static semantic analysis for web components.
4. **`Conventional PR Title`**: Pull request title conventional commits validator.
5. **`PR Description & Checklist Readiness`**: PR template and completeness check.
6. **`Static Security Lint & Boundaries`**: Bandit AST security check and architectural boundary tests.
7. **`Deterministic Hash & DAG Regression`**: Deterministic graph and fingerprint tests.
8. **`PostgreSQL Ephemeral Service`**: Multi-dialect integration tests against real PostgreSQL services.
9. **`SQLite Integration`**: File and in-memory SQLite schema discovery validation.
10. **`TypeScript Quality`**: TypeScript strict typechecking and ESLint linting.
11. **`Python Tests (3.12)`**: Automated test suite on Python 3.12.
12. **`Python Tests (3.13)`**: Automated test suite on Python 3.13.

### D. History & Integrity

| Setting | Recommended Value | Rationale |
|---|---|---|
| **Require linear history** | **Enabled** | Preserves bisectable git history; enforces squash merging. |
| **Require signed commits** | **Enabled (Advisory)** | Cryptographic verification of commit authors. |
| **Block force pushes** | **Enabled** | Protects immutable commit history on `main`. |
| **Block deletions** | **Enabled** | Prevents accidental deletion of the primary branch. |

---

## 3. Merge Strategy Enforcement

Under **Repository Settings > General > Pull Requests**:
- **Allow squash merging:** **Enabled** (Default commit message: **Pull request title and description**)
- **Allow merge commits:** **Disabled**
- **Allow rebase merging:** **Disabled**
- **Automatically delete head branches:** **Enabled**

This configuration guarantees that every merge into `main` creates exactly one clean Conventional Commit corresponding to the approved PR.
