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

Configure the following exact job names as **Required** in GitHub branch protection:

1. `CI Gate` (`ci.yml`) — Aggregates Python matrix and TypeScript typecheck.
2. `Conventional PR Title` (`pr-title.yml`) — Enforces Conventional Commit format.
3. `PR Description & Checklist Readiness` (`pr-readiness.yml`) — Validates completeness.
4. `Security Scan | python` (`codeql.yml`) — Advanced SAST scan for Python.
5. `Security Scan | javascript-typescript` (`codeql.yml`) — SAST scan for TypeScript.
6. `Internal Markdown Link & Structure Check` (`documentation.yml`) — Markdown integrity.
7. `10-Language Parity & RTL Verification` (`i18n.yml`) — Multilingual documentation.
8. `Deterministic Hash & DAG Regression` (`schema-regression.yml`) — Schema hash regression.

---

## 3. Pull Request Merge Strategy

DERA standardizes on **Squash and Merge** (or **Rebase and Merge**) using the verified Conventional Commit PR title as the resulting commit message on `main`.
