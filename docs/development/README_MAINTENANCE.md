# README Maintenance & Documentation Lifecycle Contract

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Lead Maintainer:** [Krishanth](https://github.com/krishanth7) (`@krishanth7`)  
**Standard:** Open-Source Documentation Governance & Quality Assurance  

---

## 1. Purpose & Scope

This document establishes the official documentation maintenance contract for DERA. It defines operational rules for keeping the primary English [`README.md`](../../README.md), secondary guides in [`docs/`](../README.md), and multilingual translations in [`docs/i18n/`](../i18n/README.en.md) synchronized, accurate, accessible, and grounded in working repository code.

---

## 2. English as the Primary Source of Truth

1. **Authoritative Master:** The root [`README.md`](../../README.md) is the primary, authoritative entry point for all DERA technical documentation.
2. **Translation Precedence:** When discrepancies occur between translations and the English README, the English documentation takes immediate precedence.
3. **Synchronization Flow:** All feature additions, architectural updates, command changes, and security guidelines must first be committed and verified in English before triggering international localization in Phase 2.2+.

---

## 3. Feature Status & Truth-in-Documentation Policy

DERA enforces a strict **Truth-in-Documentation** standard:

| Allowed Status Label | Exact Meaning | Required Repository Evidence |
|:---|:---|:---|
| **`Implemented`** | The capability is fully coded, functional, and backed by passing automated tests. | Source file path in `packages/` or `apps/` + passing unit/integration test in `tests/`. |
| **`Experimental`** | The code exists and runs, but the API or data model is subject to breaking changes. | Source code present in tree + prototype tests. |
| **`In Progress`** | Active engineering work is taking place on a development branch or PR. | Active PR, test harness, or integration service in `tests/integration/`. |
| **`Planned`** | Scheduled for future implementation in DERA's [12-Phase Roadmap](../roadmap/README.md). | Roadmap milestone target; no speculative claim of current functionality. |

> [!WARNING]
> Contributors and maintainers must **never** mark a feature as `Implemented` solely because its documentation, directory skeleton, or roadmap prompt exists. Every claim must trace directly to verified source code.

---

## 4. Documentation Requirements for Pull Requests

Every pull request modifying repository functionality must update relevant documentation as part of the PR's definition of done:

1. **New Database Connectors:** Must update the Database Compatibility Matrix in `README.md` and add dialect instructions in `docs/architecture/`.
2. **Data Contract Changes:** Must document schema modifications in `packages/contracts/` and update `docs/architecture/MODULE_BOUNDARIES.md`.
3. **CLI / Command Modifications:** Must update command references in `README.md`, `docs/development/COMMANDS.md`, and `docs/development/GETTING_STARTED.md`.
4. **Security Mitigations:** Must document attack vector resolutions in `docs/security/`.
5. **PR Checklist Verification:** The PR author and reviewers must verify that documentation link checks (`validate_docs.py`) pass before merge.

---

## 5. Automated Documentation Link & Structure Validation

Documentation integrity is strictly enforced via CI:
- **Script:** [`scripts/ci/validate_docs.py`](../../scripts/ci/validate_docs.py)
- **CI Workflow:** [`.github/workflows/documentation.yml`](../../.github/workflows/documentation.yml)
- **Rules:**
  1. All relative links between markdown files must resolve to existing files.
  2. Anchor fragments (`#heading-id`) must correspond to valid markdown headings.
  3. Image and badge URLs must be accessible and valid.
  4. Local execution via cross-platform runner:
     ```bash
     python scripts/development/dev.py validate-docs
     ```

---

## 6. Translation Synchronization Triggers

International translations in [`docs/i18n/`](../i18n/) are synchronized according to the following triggers:

1. **Major / Minor Release:** Prior to tagging a new version (e.g. `v0.2.0`), all 9 international README translations (Spanish, French, German, Portuguese, Italian, Japanese, Korean, Simplified Chinese, Russian) must be reviewed and synchronized with the English README.
2. **Significant Architectural Changes:** When core architecture diagrams, quick-start workflows, or security principles are updated, a translation tracking issue is automatically created under the `type/docs` label.
3. **Terminology Parity:** All translations must maintain strict terminology parity defined in [`docs/i18n/TERMINOLOGY.md`](../i18n/TERMINOLOGY.md) and adhere to [`docs/i18n/TRANSLATION_POLICY.md`](../i18n/TRANSLATION_POLICY.md).

---

## 7. Badge & CI Status Verification

1. **Real Target Links:** Every badge displayed in `README.md` must link to its corresponding active workflow, configuration, or license document.
2. **Dynamic Workflows:** CI badges must dynamically reflect the `main` branch status from GitHub Actions (e.g. `ci.yml`, `codeql.yml`, `documentation.yml`).
3. **No Decorative Fake Badges:** Badges claiming static test passage without active CI backing are strictly prohibited.

---

## 8. Deprecation & Cleanup Policy

1. Outdated installation steps, abandoned commands, and legacy configuration templates must be removed promptly.
2. Deprecated documentation files must be archived in `docs/audit/` or removed from active navigation to prevent developer confusion.
3. When renaming documents, internal links across all 69+ markdown files must be updated simultaneously.
