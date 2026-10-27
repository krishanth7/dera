# DERA Documentation & Internationalization CI Architecture

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Classification:** Official DevSecOps Documentation & CI Architecture Guide  
> **Translation Governance Reference:** [`docs/i18n/TRANSLATION_POLICY.md`](../i18n/TRANSLATION_POLICY.md)  

---

## 1. Overview & Architectural Principles

DERA enforces a strict, deterministic, and layered continuous integration architecture for documentation and multilingual localization.

The documentation CI system is architected around four core design principles:
- **Consolidated Responsibilities:** Clear boundaries separating core document formatting (`documentation.yml`) from multilingual localization (`i18n.yml`) to eliminate duplicate job execution.
- **Hermetic & Fast Execution:** All required PR checks run 100% offline in under 45 seconds without external network dependencies.
- **Least-Privilege Security:** Strict read-only tokens (`permissions: contents: read`) with zero write tokens or secret access.
- **Fork Contributor Safety:** PRs from community forks execute cleanly without requiring repository secrets or write permissions.

---

## 2. Documentation Workflows Matrix

```mermaid
flowchart TD
    PR[Pull Request / Push to main] --> DOCS[DERA | Documentation Validation]
    PR --> I18N[DERA | Multilingual Validation]
    CRON[Weekly Schedule / Manual] --> EXT[DERA | External Link Health Check]

    subgraph CoreQuality["1. Documentation Validation (documentation.yml)"]
        D1[Markdown Linting\nmarkdownlint-cli2]
        D2[Internal Links & Anchors\nvalidate_docs.py]
        D3[Mermaid Syntax\nvalidate_mermaid.py]
        D4[Regression Tests\ntest_doc_validation.py]
    end

    subgraph Multilingual["2. Multilingual Validation (i18n.yml)"]
        I1[Language Manifest & Nav Check\ngenerate_language_navigation.py]
        I2[Translation Parity & Tokens\nvalidate_i18n.py]
        I3[i18n Regression Tests\ntest_i18n_parity.py]
    end

    subgraph NetworkAudit["3. External Link Audit (external-links.yml)"]
        E1[Isolated HTTP/HTTPS Checker\nvalidate_external_links.py]
    end

    DOCS --> CoreQuality
    I18N --> Multilingual
    EXT --> NetworkAudit
```

| Workflow File | Workflow Name | Job / Check Name | Triggers | Scope | Status Gate |
|---|---|---|---|---|:---:|
| [`.github/workflows/documentation.yml`](../../.github/workflows/documentation.yml) | `DERA \| Documentation Validation` | `Documentation Quality Gates` | `push`, `pull_request` (`opened`, `synchronize`, `reopened`, `ready_for_review`), `workflow_dispatch` | Markdown syntax, links, anchors, Mermaid syntax, document structure | **Required** |
| [`.github/workflows/i18n.yml`](../../.github/workflows/i18n.yml) | `DERA \| Multilingual Validation` | `10-Language Parity & Navigation Verification` | `push`, `pull_request` (`opened`, `synchronize`, `reopened`, `ready_for_review`), `workflow_dispatch` | Canonical manifest, 10-language navigation, structural parity, token preservation | **Required** |
| [`.github/workflows/external-links.yml`](../../.github/workflows/external-links.yml) | `DERA \| External Link Health Check` | `External Link Health Check` | Schedule (`0 4 * * 1`), `workflow_dispatch` | External HTTP/HTTPS URLs with retries, timeouts, and documented exclusions | **Informational** (Decoupled) |

---

## 3. Workflow Details & Responsibilities

### 3.1 DERA Documentation Validation (`documentation.yml`)
- **Triggers:** Pull requests and pushes targeting `main` touching `docs/**`, `*.md`, `.markdownlint-cli2.jsonc`, `scripts/ci/validate_docs.py`, `scripts/ci/validate_mermaid.py`, or `tests/docs/test_doc_validation.py`.
- **Concurrency:** `cancel-in-progress: true` automatically supersedes obsolete runs on rapid commits.
- **Job Steps:**
  1. **Markdown Linting:** Executes `markdownlint-cli2` across all markdown files adhering to `.markdownlint-cli2.jsonc`.
  2. **Internal Links & Anchors:** Runs `scripts/ci/validate_docs.py` to verify case-sensitive path resolution, GitHub heading anchor slugs, and mandatory entry points.
  3. **Mermaid Diagram Syntax:** Runs `scripts/ci/validate_mermaid.py` to parse all fenced Mermaid blocks and verify type declarations, balanced blocks, and unclosed quotes.
  4. **Regression Tests:** Executes `tests/docs/test_doc_validation.py`.

### 3.2 DERA Multilingual Validation (`i18n.yml`)
- **Triggers:** Pull requests and pushes targeting `main` touching `README.md`, `docs/README.md`, `docs/i18n/**`, `scripts/docs/**`, `scripts/ci/validate_i18n.py`, or `tests/docs/test_i18n_*.py`.
- **Job Steps:**
  1. **Navigation Synchronization:** Executes `scripts/docs/generate_language_navigation.py --check` verifying that all 12 managed documents have synchronized navigation matching `languages.json`.
  2. **Translation Parity & Token Preservation:** Executes `scripts/ci/validate_i18n.py` verifying:
     - Exact 10 official languages (`en`, `es`, `fr`, `de`, `pt`, `it`, `ja`, `ko`, `zh-CN`, `ru`).
     - Rejection of excluded languages (`ar`, `hi`, `te`, `ta`, etc.).
     - Code block count and sequence parity across all 9 translations.
     - Section count parity (15 major H2 sections).
     - Non-translatable technical token preservation (`DERA`, `packages/core`, `apps/api`, etc.).
  3. **Multilingual Regression Tests:** Runs `tests/docs/test_language_navigation.py` and `tests/docs/test_i18n_parity.py`.

### 3.3 External Link Health Check (`external-links.yml`)
- **Purpose:** Decouples external network verification from PR qualification. External website downtime, network blips, or CDN rate limits never block pull request merges.
- **Schedule:** Runs every Monday at 04:00 UTC.
- **Exclusions:** Explicitly skips authenticated GitHub advisory creation URLs, loopback addresses (`127.0.0.1`), RFC 2606 example domains, and rate-limited shields badges.

---

## 4. Fork Behavior & Security Boundaries

- **Zero Secret Exposure:** Documentation workflows never access repository secrets or deployment keys.
- **No `pull_request_target`:** Pull requests from external forks execute under standard unprivileged `pull_request` runners with read-only tokens.
- **No In-Workflow Mutations:** Generator check mode (`--check`) operates in non-mutating validation mode during CI. Workflows never automatically commit changes back to contributor branches.

---

## 5. Troubleshooting & Common Failures

### 1. Navigation Out of Sync
- **Error:** `Navigation content out of sync with languages.json`
- **Cause:** A README file has modified or missing language navigation links.
- **Remediation:** Run `python scripts/docs/generate_language_navigation.py --write` to re-synchronize all 12 documents.

### 2. Broken Anchor or Case Mismatch
- **Error:** `DOC-ANCH-004: Anchor '#catalog-inspection' not found in target file 'README.md'`
- **Cause:** Heading text was renamed or casing differs on disk.
- **Remediation:** Run `python scripts/ci/validate_docs.py` to identify the broken reference and correct the heading slug.

### 3. Translation Structural Parity Failure
- **Error:** `docs/i18n/README.es.md: Code block count mismatch: expected 250, found 248`
- **Cause:** A code block was deleted or unclosed in the translated file.
- **Remediation:** Ensure all code blocks and Mermaid diagrams from the English root `README.md` are preserved in the localized document.

---

## 6. Maintenance & Ownership

- **Ownership:** Maintained by Bunga Krishanth (`@krishanth7`) and the DERA Internationalization & CI working group.
- **Policy Reference:** Review [`docs/i18n/TRANSLATION_MAINTENANCE.md`](../i18n/TRANSLATION_MAINTENANCE.md) and [`docs/i18n/TRANSLATION_POLICY.md`](../i18n/TRANSLATION_POLICY.md) for translation change management.
