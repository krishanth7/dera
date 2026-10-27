# Phase 3.2 Pull Request Qualification & Governance Acceptance Report

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Phase:** 3 — GitHub Actions & DevSecOps  
> **Sub-phase:** 3.2 — PR Title & Readiness Validation  
> **Baseline Commit:** `ef92be991c96c4d4792df5907aca808b0732f75e`  
> **Target Branch:** `main`  
> **Working Branch:** `ci/phase-3.2-pr-governance`  
> **Verification Date:** 2026-10-27  
> **Acceptance Status:** **VERIFIED & ACCEPTED**

---

## 1. Executive Summary

Phase 3.2 establishes DERA's authoritative, enterprise-grade pull request title validation and review readiness governance system. The implementation guarantees deterministic, contributor-friendly qualification across all community and core pull requests without reliance on artificial intelligence, non-deterministic LLM reviewers, or privileged external services.

All contributor-supplied text (PR titles, descriptions, branch names, metadata) is treated strictly as **untrusted user input**, preventing command injection, expression interpolation vulnerabilities, and token compromise.

---

## 2. Baseline Audit & Key Findings

Prior to implementation, a full baseline audit of existing PR validation mechanisms was performed and recorded in [`docs/audit/PHASE_3_2_PR_GOVERNANCE_BASELINE.md`](./PHASE_3_2_PR_GOVERNANCE_BASELINE.md):

| Finding Area | Pre-Phase 3.2 State | Phase 3.2 Remediated State |
|---|---|---|
| **Scope Vocabulary** | Restrictive list missing common domains (`cli`, `docker`, `github`) | Comprehensive canonical scope list with hierarchical and compound support |
| **Breaking Changes** | Inconsistent syntax support for `!` marker | Full Conventional Commits 1.0.0 breaking change syntax (`type(scope)!:`, `type!:`) |
| **Draft Lifecycle** | Missing `ready_for_review` and `converted_to_draft` triggers | Workflow triggers and Python validator handle draft lifecycle with non-blocking advisories |
| **Boilerplate Stripping** | Unfilled templates could pass length checks | Robust comment, header, and unchecked checkbox stripping to isolate genuine user substance |
| **Testing State** | Rigid checkbox required even for doc fixes | Multi-state testing verification (`Relevant tests passed`, `Tests not applicable`, `Tests not run`) |
| **Regression Tests** | Limited unit test coverage | 23 comprehensive regression tests in `tests/ci/` alongside existing unit tests |

---

## 3. Implemented Governance Components

### 3.1 Conventional Commit Title Validation Engine
- **Engine Location:** `scripts/ci/validate_pr_title.py`
- **Specification:** Conventional Commits 1.0.0
- **Syntax:** `type(scope): description`, `type(scope)!: description`, `type: description`, `type!: description`
- **Allowed Types:** `feat`, `fix`, `docs`, `ci`, `test`, `refactor`, `perf`, `build`, `chore`, `revert`
- **Canonical Scopes:** `core`, `api`, `web`, `contracts`, `cli`, `connectors`, `database`, `sqlite`, `postgres`, `postgresql`, `mysql`, `mariadb`, `models`, `erd`, `graph`, `diagnostics`, `docs`, `i18n`, `security`, `ci`, `governance`, `architecture`, `release`, `deps`, `repo`, `python`, `npm`, `github`, `actions`, `docker` (plus compound and slash-separated scopes)
- **Formatting Checks:** Lowercase type, lowercase initial description character, trailing period prohibition, meaningful character length, Unicode safety.
- **Workflow:** `.github/workflows/pr-title.yml` triggering on `opened`, `edited`, `reopened`, `synchronize`, `ready_for_review`, and `converted_to_draft`.

### 3.2 Draft-Aware PR Readiness Validation Engine
- **Engine Location:** `scripts/ci/validate_pr_readiness.py`
- **Boilerplate Stripping:** Strips HTML comments (`<!-- ... -->`), markdown section headers (`## ...`), and unchecked template options (`- [ ] ...`) before verifying user substance (>= 30 characters).
- **Draft Behavior:** Non-blocking advisory evaluation for drafts, allowing early feedback without failing CI status. Automatically enforces full readiness when transitioned to `ready_for_review`.
- **Testing Verification:** Validates explicit declarations across `Relevant tests passed`, `Tests not applicable`, or `Tests not run` with required explanations.
- **Security Assessment:** Mandatory security impact assessment for security-titled or security-labeled PRs.
- **Breaking Change Alignment:** Ensures breaking changes indicated by `!` in title are documented in the body.
- **Workflow:** `.github/workflows/pr-readiness.yml` triggering on `opened`, `edited`, `reopened`, `synchronize`, `ready_for_review`, and `converted_to_draft`.

### 3.3 Pull Request Template Standardization
- **Location:** `.github/PULL_REQUEST_TEMPLATE.md`
- **Structure:**
  - `## Summary`
  - `## Change Type`
  - `## Related Issues`
  - `## Implementation Details`
  - `## Testing` (with actionable checkboxes and test evidence section)
  - `## Documentation Impact`
  - `## Security Impact` (with non-AI and read-only confirmations)
  - `## Breaking Changes`
  - `## Contributor Checklist`

---

## 4. Security & Trust Boundaries Verification

The pull request governance architecture adheres strictly to GitHub Actions DevSecOps best practices:

1. **Least-Privilege Permissions:** All PR validation workflows specify top-level `permissions: contents: read`. No write permissions are granted.
2. **Zero Shell Interpolation:** All untrusted user content is transferred to Python scripts strictly via mapped environment variables (`env: PR_TITLE: ${{ github.event.pull_request.title }}`). No direct expression interpolation occurs inside inline shell scripts.
3. **Fork Isolation:** Neither workflow requests repository secrets or administrative tokens. Pull requests from community forks execute under identical, unprivileged sandboxed runners.
4. **Deterministic & Safe Execution:** No dynamic execution (`eval`, `exec`) or unsafe deserialization is employed.

---

## 5. Verification & Test Telemetry

### 5.1 Unit and Regression Test Execution

```text
Ran 86 tests in 0.441s
OK (skipped=2)
```

#### Detailed Breakdown
- `tests/ci/test_pr_title.py`: **11 tests passed** (types, scopes, breaking changes, unicode, long titles, shell metacharacters, Markdown injection, bot bypasses, syntax errors)
- `tests/ci/test_pr_readiness.py`: **12 tests passed** (boilerplate stripping, drafts, empty body, untouched templates, testing states, security disclosures, breaking change alignment, bot bypasses)
- `tests/unit/test_validate_pr_title.py`: **7 tests passed** (legacy unit suite parity)
- `tests/unit/test_validate_pr_readiness.py`: **8 tests passed** (legacy unit suite parity)
- Other repository tests: **48 tests passed** (core models, topological sort, connectors, CLI)

### 5.2 Linting & Formatting Verification

- Python syntax and formatting verified via `ruff`.
- Documentation links and navigation verified.

---

## 6. Deliverables Matrix

| Deliverable | Path | Status |
|---|---|---|
| Baseline Governance Audit | `docs/audit/PHASE_3_2_PR_GOVERNANCE_BASELINE.md` | Complete |
| PR Qualification Acceptance | `docs/audit/PHASE_3_2_PR_QUALIFICATION.md` | Complete |
| Contributor Qualification Guide | `docs/ci/PR_QUALIFICATION.md` | Complete |
| PR Title Validator Engine | `scripts/ci/validate_pr_title.py` | Complete |
| PR Readiness Validator Engine | `scripts/ci/validate_pr_readiness.py` | Complete |
| PR Title Workflow | `.github/workflows/pr-title.yml` | Complete |
| PR Readiness Workflow | `.github/workflows/pr-readiness.yml` | Complete |
| Standardized PR Template | `.github/PULL_REQUEST_TEMPLATE.md` | Complete |
| Title Regression Test Suite | `tests/ci/test_pr_title.py` | Complete |
| Readiness Regression Test Suite| `tests/ci/test_pr_readiness.py` | Complete |
| Contributor Process Integration | `CONTRIBUTING.md` | Complete |
| CI Navigation Update | `docs/ci/README.md` | Complete |

---

## 7. Definition of Done & Acceptance Sign-off

- [x] Repository baseline audited and documented
- [x] Conventional Commit title policy implemented and verified
- [x] Approved types and canonical scopes documented
- [x] Breaking-change syntax (`!`) supported and aligned with readiness
- [x] Title validator operational with actionable diagnostic output
- [x] Draft PR policy implemented with non-blocking advisories
- [x] PR template standardized and contributor-friendly
- [x] Readiness validator operational with boilerplate stripping
- [x] Workflows use least-privilege permissions (`contents: read`)
- [x] Untrusted PR content handled safely via environment variables
- [x] Comprehensive regression tests created and passing (100% pass rate)
- [x] Contributor documentation authored and linked
- [x] Reviewable pull request prepared for maintainer review

**Sign-off:** Bunga Krishanth (`@krishanth7`)  
**Status:** **ACCEPTED AND READY FOR PULL REQUEST REVIEW**
