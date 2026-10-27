# DERA Phase 3.4 — Documentation & Internationalization CI Baseline Audit

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Phase:** 3 — GitHub Actions & DevSecOps  
> **Sub-phase:** 3.4 — Documentation & Internationalization Workflows  
> **Audit Date:** 2026-10-27  
> **Classification:** Official DevSecOps Quality & Internationalization Audit  

---

## 1. Executive Summary

Sub-phase 3.4 establishes DERA's authoritative documentation and internationalization continuous integration system.

DERA maintains a 126-document markdown engineering corpus, 59 Mermaid architectural diagrams, and exactly **ten official documentation languages** (`en`, `es`, `fr`, `de`, `pt`, `it`, `ja`, `ko`, `zh-CN`, `ru`) governed by [`docs/i18n/languages.json`](../i18n/languages.json).

This baseline audit evaluates:
1. Current workflow configurations (`documentation.yml`, `i18n.yml`, `external-links.yml`, and `ci.yml`).
2. Redundant job execution and validation overlap.
3. Link, anchor, and Mermaid syntax validation mechanisms.
4. Multilingual navigation generator synchronization and managed region integrity.
5. Translation structural parity and technical token preservation.
6. Execution latency, caching, and least-privilege permissions.

---

## 2. Baseline Workflow Inventory & Architecture

| Workflow File | Name | Triggers | Execution Scope |
|---|---|---|---|
| [`.github/workflows/documentation.yml`](../../.github/workflows/documentation.yml) | `DERA \| Documentation Validation` | `push`, `pull_request` (path-filtered), `workflow_dispatch` | Markdown linting, `validate_docs.py`, `validate_mermaid.py`, `generate_language_navigation.py --check`, `validate_i18n.py`, `tests/docs/` |
| [`.github/workflows/i18n.yml`](../../.github/workflows/i18n.yml) | `DERA \| Multilingual Validation` | `push`, `pull_request` (path-filtered), `workflow_dispatch` | `generate_language_navigation.py --check`, `validate_i18n.py`, `tests/docs/test_language_navigation.py` |
| [`.github/workflows/external-links.yml`](../../.github/workflows/external-links.yml) | `DERA \| External Link Health Check` | Weekly schedule (`cron: "0 4 * * 1"`), `workflow_dispatch` | Offline from PR gates; checks external HTTP/HTTPS URLs via `validate_external_links.py` |
| [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) | `DERA CI` (`documentation-quality` job) | `push`, `pull_request` | Runs `npm run docs:check` as a required status check for the PR qualification gate |

---

## 3. Baseline Audit Findings

### DOC-BASE-01: Duplicate Validation Between `documentation.yml` and `i18n.yml`
* **Severity:** Medium
* **Category:** Workflow Consolidation & Runner Efficiency
* **Evidence:**
  * `.github/workflows/documentation.yml` executes steps:
    * `python scripts/docs/generate_language_navigation.py --check`
    * `python scripts/ci/validate_i18n.py`
    * `python -m unittest discover tests/docs/`
  * `.github/workflows/i18n.yml` executes identical steps:
    * `python scripts/docs/generate_language_navigation.py --check`
    * `python scripts/ci/validate_i18n.py`
    * `python -m unittest tests/docs/test_language_navigation.py`
  * Whenever a pull request touches `README.md` or `docs/i18n/**`, both workflows run concurrently on separate runner VMs, repeating the exact same validations and consuming double GitHub Actions minutes.
* **Remediation:**
  * Consolidate responsibility boundaries:
    * `.github/workflows/documentation.yml`: Focus strictly on core document quality (Markdown linting via `markdownlint-cli2`, internal links, heading anchors, Mermaid diagram syntax, and documentation directory structure).
    * `.github/workflows/i18n.yml`: Focus strictly on the 10-language multilingual ecosystem (canonical manifest integrity, navigation check mode, translation structural parity, token preservation, and i18n unit tests).
* **Status:** Resolved in Phase 3.4.

---

### DOC-BASE-02: Absence of Automated Translation Structural Parity Checks
* **Severity:** Medium
* **Category:** Translation Quality & Parity
* **Evidence:**
  * Existing `scripts/ci/validate_i18n.py` verifies the top-level navigation bar line (`<!-- DERA:I18N_NAV:START --> ... <!-- DERA:I18N_NAV:END -->`) and `languages.json`.
  * It does not parse or compare the body of the 9 translations against the authoritative English `README.md`.
  * If a translation accidentally omits the Feature Status Matrix, drops the Architecture Mermaid block, or deletes installation instructions, existing CI passes without warning.
* **Remediation:**
  * Expand `validate_i18n.py` and implement `tests/docs/test_i18n_parity.py` to verify:
    1. Key section presence (Overview, Capabilities, Architecture, Directory Structure, Quick Start, Database Compatibility, Security, Roadmap, License).
    2. Code fence parity (presence of executable bash, python, sql, and mermaid blocks).
    3. Structural table presence.
* **Status:** Resolved in Phase 3.4.

---

### DOC-BASE-03: Lack of Non-Translatable Technical Token Verification
* **Severity:** Low
* **Category:** Technical Token Integrity
* **Evidence:**
  * Per [`docs/i18n/TRANSLATION_MAINTENANCE.md`](../i18n/TRANSLATION_MAINTENANCE.md) Section 3.1, CLI commands, package paths (`packages/core`, `packages/connectors`, `apps/api`, `apps/web`), and core tokens must never be localized.
  * No automated regression test currently verifies token preservation across translations.
* **Remediation:**
  * Add automated token verification in `validate_i18n.py` scanning all 9 translations for essential technical identifiers.
* **Status:** Resolved in Phase 3.4.

---

### DOC-BASE-04: Lack of Unified Diagnostic Domain Summary in CI Output
* **Severity:** Low
* **Category:** Developer Experience & Contributor Feedback
* **Evidence:**
  * Validation scripts output independent status strings (`SUCCESS: All 126 markdown documentation files passed validation.`) without a structured, domain-by-domain diagnostic dashboard.
  * When failures occur, contributors must parse raw stack traces rather than seeing an actionable domain breakdown.
* **Remediation:**
  * Standardize structured summary reporting matching Phase 3.4 specifications across documentation and i18n tooling.
* **Status:** Resolved in Phase 3.4.

---

### DOC-BASE-05: External Link Isolation (Verified Correct Design)
* **Severity:** Informational (Pass)
* **Category:** Architectural Best Practice
* **Evidence:**
  * External HTTP/HTTPS link checking is decoupled into [`.github/workflows/external-links.yml`](../../.github/workflows/external-links.yml) running on a weekly schedule (`cron: "0 4 * * 1"`).
  * PR qualification gates remain 100% offline, hermetic, and fast (< 45s).
* **Remediation:** Retain isolated architecture.
* **Status:** Confirmed.

---

## 4. Security & Permissions Review

* **Default Permissions:** All documentation workflows declare `permissions: contents: read`.
* **Zero Elevated Secrets:** Neither `documentation.yml` nor `i18n.yml` requests repository secrets or tokens.
* **Zero `pull_request_target`:** Pull requests from external forks execute under standard unprivileged `pull_request` runners with read-only access.
* **Hermetic Execution:** Offline execution guarantees zero risk of token exfiltration or dependency poisoning.

---

## 5. Baseline Metric Summary

* **Total Markdown Documents Scanned:** 126
* **Total Mermaid Diagrams Scanned:** 59
* **Official Languages Configured:** 10 (`en`, `es`, `fr`, `de`, `pt`, `it`, `ja`, `ko`, `zh-CN`, `ru`)
* **Excluded Languages Blocked:** Arabic (`ar`), Indian regional languages (`hi`, `te`, `ta`, `kn`, etc.)
* **Current Documentation Unit Tests:** 31 tests (passing in 0.230s)
* **Target Documentation Unit Tests:** >= 40 tests covering parity, tokens, drift, and traversal.
