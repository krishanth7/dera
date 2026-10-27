# DERA Branch Protection & Merge Rulesets

To ensure repository integrity and prevent unverified code from reaching production, this document defines the recommended GitHub branch protection rules and required status checks for the `main` branch.

---

## 1. Recommended Ruleset Configuration for `main`

Navigate to **Settings → Branches → Add classic branch protection rule** (or **Rules → Rulesets → New ruleset**) on GitHub:

| Setting | Recommended Value | Purpose |
|---|---|---|
| **Branch name pattern** | `main` | Protect primary production branch |
| **Require a pull request before merging** | **Enabled** | Prevents direct pushes to production |
| **Required approvals** | `1` | At least one maintainer code review |
| **Dismiss stale pull request approvals** | **Enabled** | New commits re-trigger review requirement |
| **Require status checks to pass before merging** | **Enabled** | Enforces CI gate passing |
| **Require branches to be up to date before merging** | **Enabled** | Prevents race condition regressions |
| **Require conversation resolution before merging** | **Enabled** | Ensures all review feedback is resolved |
| **Require linear history** | **Enabled** | Keeps git history clean (squash or rebase) |
| **Do not allow bypassing the above settings** | **Enabled** | Applies rules uniformly to maintainers |
| **Allow force pushes** | **Disabled** | Protects permanent git commit history |
| **Allow deletions** | **Disabled** | Prevents accidental branch deletion |

---

## 2. Stable Required Status Check Names

To prevent pull requests from hanging due to path-filtered triggers, DERA separates **Always Required Qualification Checks** (which execute on every pull request targeting `main`) from **Conditional / Path-Filtered Checks**:

### A. Always Required for Merge (Configured in Branch Protection)

1. **`Qualification Gate`** (`ci.yml`) — Authoritative aggregate gate evaluating Python 3.12 & 3.13, Frontend builds, Contracts & boundaries, Database integration (SQLite + Postgres 16), and full Documentation quality.
2. **`Conventional PR Title`** (`pr-title.yml`) — Validates pull request title adherence to Conventional Commits.
3. **`PR Description & Checklist Readiness`** (`pr-readiness.yml`) — Validates description length, testing explanation, and security declarations.

### B. Conditional / Specialized Quality Checks

These specialized checks trigger on targeted file path modifications or cron schedules to provide fast localized feedback:
- `Security Scan | python` (`codeql.yml`)
- `Security Scan | javascript-typescript` (`codeql.yml`)
- `Documentation Quality Gates` (`documentation.yml`)
- `Deterministic Hash & DAG Regression` (`schema-regression.yml`)
- `SQLite Runtime Matrix` (`sqlite-compatibility.yml`)

---

## 3. Pull Request Merge Strategy

DERA standardizes on **Squash and Merge** (or **Rebase and Merge**) using the verified Conventional Commit PR title as the resulting commit message on `main`.
