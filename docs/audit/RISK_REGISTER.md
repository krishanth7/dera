# DERA Engineering Risk Register

> **Phase:** 1.1 Technical Audit  
> **Audited Commit:** [`52dcc8df395f464172ea019b3df716e36b62134f`](https://github.com/krishanth7/dera/commit/52dcc8df395f464172ea019b3df716e36b62134f)  

---

## 1. Risk Evaluation Methodology

Risks are categorized across eight engineering dimensions and ranked by **Severity** (`Critical`, `High`, `Medium`, `Low`, `Informational`) based on their likelihood and impact on platform integrity, security, and developer velocity.

---

## 2. Risk Register Matrix

| Risk ID | Category | Risk Description | Severity | Verifiable Evidence | Mitigation Strategy | Target Owner / Phase |
|---|---|---|---|---|---|---|
| **RSK-01** | **Security** | **Unprotected Default Branch (`main`)**<br>Direct pushes, unreviewed PR merges, and history rewrites are possible. | **Critical** | `gh api /branches/main/protection` returned `HTTP 404: Branch not protected`. | Configure GitHub Repository Ruleset on `main` requiring PR review, linear history, and required status checks. | **Phase 1.3** (DevSecOps) |
| **RSK-02** | **CI/CD** | **Single Point of Verification on `main`**<br>`main` currently only runs CodeQL; unit tests and type checks do not run on push to `main` until PR #3 merges. | **High** | Only `codeql.yml` exists under `.github/workflows/` on `main`. | Merge PR #3 to deploy `ci.yml`, `docs-validate.yml`, and `schema-regression.yml` to `main`. | **Phase 1.3** (DevSecOps) |
| **RSK-03** | **Security** | **Permissive Default Action Permissions**<br>Workflows lack top-level `permissions: read-all` restriction. | **Medium** | `.github/workflows/codeql.yml` does not declare global read-only permissions block. | Add explicit `permissions: contents: read` to all workflow heads. | **Phase 1.3** (DevSecOps) |
| **RSK-04** | **Database Access** | **Potential Accidental DDL Mutation**<br>Database connectors could execute mutating queries if read-only boundaries fail. | **High** | No formal SQL read-only statement whitelisting in core connector architecture yet. | Enforce session-level `SET TRANSACTION READ ONLY` and AST validation via SQLGlot to reject DDL/DML. | **Phase 5** (Connectors) |
| **RSK-05** | **Supply Chain** | **Unfrozen Python Package Dependencies**<br>Lack of lockfile in Python environment risks build breakage from minor/patch upstream releases. | **Medium** | `pyproject.toml` uses `>=` version specifiers with no `requirements.lock` on `main`. | Generate frozen lockfile using `uv.lock` or `pip-compile` for production container images. | **Phase 1.4** (Packaging) |
| **RSK-06** | **Architecture** | **Non-Deterministic Cycle Traversal Drift**<br>Cycle detection algorithms could produce fluctuating path orders if node iterations rely on set ordering. | **Medium** | Python set iteration order can vary across runs without sorting. | Ensure all adjacency list iterations and cycle path representations sort table names deterministically. | **Phase 1.2** (Core Hardening) |
| **RSK-07** | **Documentation** | **Unclear Implementation Boundaries**<br>Users might expect cloud PostgreSQL/Snowflake inspection to work immediately out of the box. | **Medium** | Root README lists capabilities without a status column per database engine. | Add clear "Engine Support Status" matrix table to root README distinguishing released vs planned. | **Phase 1.2** (Docs) |
| **RSK-08** | **Operational** | **Stale GitHub Action Cache Bloat**<br>Large node_modules or pip caches could exceed repository storage quotas. | **Low** | Dependabot updates and multi-matrix CI runs create multiple cache keys. | Deploy `.github/workflows/cleanup-caches.yml` (included in PR #3) on weekly schedule. | **Phase 1.3** (DevSecOps) |
| **RSK-09** | **Release** | **Unsigned Artifacts & Releases**<br>Releases published without SHA-256 checksums or cryptographic signatures risk tampering. | **Medium** | No published releases or release workflows currently on `main`. | Implement automated release workflow generating SHA-256 checksums and GitHub releases (prepared in PR #3). | **Phase 1.6 / Phase 12** |

---

## 3. Confirmed Findings vs. Potential Risks

- **Confirmed Findings (Empirically Verified):**
  1. Branch protection on `main` is absent (Confirmed via GitHub API).
  2. Package lockfile is absent on `main` (Confirmed via filesystem check).
  3. No unit test workflow triggers on `main` pushes outside PR #3 (Confirmed via workflow inventory).
- **Potential Risks (Preventative Mitigations):**
  1. Accidental DDL execution against customer databases (Mitigated by design in Phase 5).
  2. Cycle detection path sorting non-determinism (Mitigated by test regression suite in PR #3).
