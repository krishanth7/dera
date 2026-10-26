# DERA Repository Baseline Manifest

> **Standard:** Phase 1.1 Baseline Specification  
> **Audit Timestamp:** `2026-10-26T08:29:15Z`  
> **Audited Commit SHA:** [`52dcc8df395f464172ea019b3df716e36b62134f`](https://github.com/krishanth7/dera/commit/52dcc8df395f464172ea019b3df716e36b62134f)  

---

## 1. Verified Repository Identity

The following identity parameters have been verified using the GitHub API and local Git refs:

| Property | Verified Value | Telemetry / Verification Source |
|---|---|---|
| **Repository Owner** | `krishanth7` (ID: `U_kgDODFSe6w`) | `gh repo view krishanth7/dera --json owner` |
| **Repository Name** | `dera` | `gh repo view krishanth7/dera --json name` |
| **Repository URL** | [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera) | `gh repo view krishanth7/dera --json url` |
| **Default Branch** | `main` | `gh repo view krishanth7/dera --json defaultBranchRef` |
| **Visibility** | `PUBLIC` (`isPrivate: false`) | `gh repo view krishanth7/dera --json visibility,isPrivate` |
| **Audited HEAD SHA** | `52dcc8df395f464172ea019b3df716e36b62134f` | `git rev-parse origin/main` |
| **Latest Commit Message** | `feat(core): implement Python and TypeScript foundations for CodeQL analysis` | `git log -1 --format=%s origin/main` |
| **Commit Author** | `Krishanth <206872299+krishanth7@users.noreply.github.com>` | `git log -1 --format=%an origin/main` |
| **Commit Timestamp** | `Mon Oct 26 13:15:29 2026 +0530` | `git log -1 --format=%cd origin/main` |
| **Working Tree State** | Clean (`nothing to commit, working tree clean`) | `git status` |
| **License** | MIT License (`spdx_id: MIT`) | `LICENSE` file & `gh api /community/profile` |
| **Releases Count** | `0` (No published releases) | `gh release list` |
| **Tags Count** | `0` (No Git tags created) | `git tag -l` |
| **Open Pull Requests** | `1` ([PR #3](https://github.com/krishanth7/dera/pull/3): `ci/dera-enterprise-workflows`) | `gh pr list --state open` |
| **Closed Pull Requests** | `2` (PR #1 merged, PR #2 closed) | `gh pr list --state closed` |
| **Open Issues** | `0` | `gh issue list --state open` |
| **Closed Issues** | `0` | `gh issue list --state closed` |

---

## 2. Source Language Inventory

The audited commit contains 46 tracked files across the following language ecosystems:

| Language / Format | Tracked Files | Primary Purpose in Baseline |
|---|---|---|
| **Python** (`.py`) | 7 | Deterministic core data models, topological DAG graph algorithms, diagnostic rules, API gateway stub |
| **TypeScript** (`.ts`) | 2 | Shared monorepo data contract types (`packages/contracts`) and web UI stub (`apps/web`) |
| **Markdown** (`.md`) | 21 | Architectural documentation, security model, contributing guidelines, and 10-language translations |
| **YAML** (`.yml`) | 7 | CodeQL security scanning, Dependabot configuration, issue and pull request templates |
| **JSON** (`.json`) | 4 | Node package configurations (`package.json`, subpackages) and TypeScript config (`tsconfig.json`) |
| **TOML** (`.toml`) | 1 | Python project packaging and metadata declaration (`pyproject.toml`) |
| **Other** (`.gitignore`, `LICENSE`) | 4 | Git ignore rules, license text, and funding definitions |

---

## 3. Workflow & CI/CD Status

- **Default Branch (`main`):** Contains 1 workflow:
  - `.github/workflows/codeql.yml` — CodeQL security analysis for Python and JavaScript/TypeScript.
- **Enterprise DevSecOps PR ([#3](https://github.com/krishanth7/dera/pull/3)):** Branch `ci/dera-enterprise-workflows` introduces 18 comprehensive workflows:
  - CI test matrix (Python 3.12, 3.13), TypeScript build, Docker multi-arch non-root build, SQLite connector test, PostgreSQL service integration, DAG determinism checks, security boundary audits, docs validation, 10-language parity checks, Dependabot auto-qualification, and release gating.
  - Verification Status: All 20 GitHub check runs on PR #3 are verified **Passing** (`pass`).

---

## 4. Test Framework Status

| Test Suite | Implementation Status | Framework / Runner | Verified Result |
|---|---|---|---|
| **Unit Tests (Core)** | Implemented | Python `unittest` | 5 tests ran, 3 passed, 2 skipped (FastAPI optional) |
| **Type Checking** | Implemented | TypeScript `tsc` (`5.x`) | Exit code `0` (`npx -p typescript tsc --noEmit`) |
| **Syntax Validation** | Implemented | Python `compileall` | Exit code `0` across `packages/`, `apps/`, `tests/` |
| **YAML Validation** | Implemented | Python `yaml.safe_load` | Exit code `0` across all 7 `.github` YAML files |
| **Integration Tests** | Foundation in PR #3 | Python / SQLite / PostgreSQL | Ready for merge into `main` |
| **E2E / Browser Tests** | Not Started | Playwright | Planned for Phase 7 (Frontend Studio) |

---

## 5. Documentation & Translation Status

- **English Root Documentation:** Complete root `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `docs/architecture/overview.md`, `docs/development/setup.md`, `docs/security/model.md`.
- **Multilingual Documentation (`docs/i18n/`):** 10 localized versions (`README.ar.md`, `README.de.md`, `README.en.md`, `README.es.md`, `README.fr.md`, `README.ja.md`, `README.ko.md`, `README.pt.md`, `README.ru.md`, `README.zh-CN.md`).
- **Community Health:** 100% health score confirmed by GitHub Community Profile API.

---

## 6. Security Profile & Posture

| Feature | Verified State | GitHub API Evidence |
|---|---|---|
| **Private Vulnerability Reporting** | `ENABLED` | `{"enabled": true}` via `/private-vulnerability-reporting` |
| **Secret Scanning** | `ENABLED` | `{"status": "enabled"}` via `/security_and_analysis` |
| **Push Protection** | `ENABLED` | `{"status": "enabled"}` via `/security_and_analysis` |
| **Dependabot Security Updates** | `ENABLED` | `{"status": "enabled"}` via `/security_and_analysis` |
| **Secret Scanning Alerts** | `0` Alerts | `[]` via `/secret-scanning/alerts` |
| **Dependabot Alerts** | `0` Alerts | `[]` via `/dependabot/alerts` |
| **CodeQL Alerts** | `0` Alerts | `[]` via `/code-scanning/alerts` |
| **Branch Protection (`main`)** | `DISABLED` (`404`) | `{"message": "Branch not protected"}` via `/branches/main/protection` |
| **Repository Rulesets** | `NONE` (`0`) | `[]` via `/rulesets` |

---

## 7. Known Baseline Limitations

1. **Branch Protection Absence:** `main` has no branch protection rulesets configured; direct pushes are technically possible until protected in Phase 1.3.
2. **Missing Package Lockfile on `main`:** `package-lock.json` is missing on `main` (though added in PR #3), requiring `-p typescript` flag for `npx` invocations.
3. **Database Drivers Not Installed:** SQLite is natively supported via Python standard library; PostgreSQL, MySQL, and Snowflake connectors require external driver dependencies (`psycopg`, `asyncpg`) to be formalized in Phase 4 and Phase 5.
4. **No Runtime Application Packaging:** No container images or PyPI/npm packages have been published yet.
