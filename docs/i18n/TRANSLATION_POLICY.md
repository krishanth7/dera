# DERA Documentation Translation & Synchronization Policy

## 1. Overview & Purpose

DERA (*Database Engineering & Reverse Analysis*) is committed to providing accurate, complete, and synchronized technical documentation for the global developer community.

This policy establishes the governance standards, synchronization triggers, parity criteria, and review requirements for maintaining DERA's multilingual documentation suite in [`docs/i18n/`](README.en.md).

---

## 2. Official Language Policy

DERA supports exactly **ten official documentation languages**:

1. **English (`en`)** — Primary authoritative source of truth ([`README.md`](../../README.md), [`docs/i18n/README.en.md`](README.en.md)).
2. **Spanish (`es`)** — [`docs/i18n/README.es.md`](README.es.md).
3. **French (`fr`)** — [`docs/i18n/README.fr.md`](README.fr.md).
4. **German (`de`)** — [`docs/i18n/README.de.md`](README.de.md).
5. **Portuguese (`pt`)** — [`docs/i18n/README.pt.md`](README.pt.md).
6. **Italian (`it`)** — [`docs/i18n/README.it.md`](README.it.md) *(replaces Arabic in the active 10-language matrix)*.
7. **Japanese (`ja`)** — [`docs/i18n/README.ja.md`](README.ja.md).
8. **Korean (`ko`)** — [`docs/i18n/README.ko.md`](README.ko.md).
9. **Simplified Chinese (`zh-CN`)** — [`docs/i18n/README.zh-CN.md`](README.zh-CN.md).
10. **Russian (`ru`)** — [`docs/i18n/README.ru.md`](README.ru.md).

### Explicit Exclusions
- **Arabic (`ar`):** Removed from the active documentation set as part of Phase 2.2.
- **Indian Regional Languages:** Hindi, Telugu, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Urdu, and other regional Indian languages are explicitly excluded from repository documentation to prevent fragmentation and maintain strict QA reviewability.
- No additional languages shall be added without formal maintainer approval.

---

## 3. English Source-of-Truth Principle

1. **Canonical Authority:** The root English [`README.md`](../../README.md) is the sole authoritative definition of DERA's architecture, feature status, security posture, installation procedures, and roadmap.
2. **Derivative Nature of Translations:** All non-English README documents are derivative works of the English primary documentation.
3. **Precedence:** In any instance of ambiguity, technical divergence, or semantic conflict between a translation and the English README, the English README takes absolute precedence.

---

## 4. Translation Synchronization Triggers

International documentation must be updated whenever any of the following triggers occur:

| Trigger Event | Impact Scope | Action Required |
|---|---|---|
| **Feature Status Change** | Capability transition (e.g. In Progress → Implemented) | Synchronize Feature Status Matrix across all 9 translations. |
| **Architectural Change** | Package boundaries, Mermaid diagram, or new apps | Update Architecture Visualization and explanatory prose. |
| **New Database Support** | Connector addition or dialect qualification | Update Database Compatibility Matrix and connection instructions. |
| **Security Principle Revision** | Vulnerability process or connection safety rules | Update Security Principles and verification disclaimers. |
| **Release Candidate (RC)** | Tagging of minor or major release (e.g. `v0.2.0`) | Full review of all 10 documentation files against [`TERMINOLOGY.md`](TERMINOLOGY.md). |

---

## 5. Structural & Content Parity Standards

Every translated README must mirror the English baseline across the following required sections:

- [x] **Top Navigation Bar:** Identical cross-language links in canonical order.
- [x] **Hero & Identity:** Name, expansion, localized tagline, and non-AI deterministic mandate.
- [x] **Verified Badges:** Matching set of dynamic GitHub Actions and licensing badges.
- [x] **Table of Contents:** Identical anchor mapping.
- [x] **Project Overview:** Engineering problems addressed and deterministic design justification.
- [x] **Feature Status Matrix:** Identical 10 capabilities, statuses, and source code citations.
- [x] **Architecture Visualization:** Identical Mermaid structure with localized component descriptions.
- [x] **Monorepo Directory Layout:** Verifiable directory tree.
- [x] **Quick Start:** Identical prerequisites table and executable CLI commands.
- [x] **Database Compatibility:** Identical engine support and limitation notes.
- [x] **Security Principles:** Identical defensive architecture rules and certification disclaimers.
- [x] **Documentation Navigation:** Complete links to architecture, development, and governance guides.
- [x] **Roadmap:** Summary of the 12-Phase master development plan.
- [x] **Contributing & Community:** Links to contribution guides, issues, discussions, and security reporting.
- [x] **License & Maintainer:** MIT License attribution and maintainer identification (`Krishanth`).

---

## 6. Prohibited Practices

1. **No Superficial Summaries:** A translation must not truncate the documentation to a high-level summary. Full parity is mandatory.
2. **No Invented Capabilities:** Translations must never claim features, performance metrics, or certifications not present in the English source.
3. **No Code Localization:** Shell commands, file paths, Python modules, TypeScript variables, and SQL statements must never be translated into local languages.
4. **No Automated Unreviewed Merge:** Machine translations must be verified against [`TERMINOLOGY.md`](TERMINOLOGY.md) and passed through CI linting before merging.

---

## 7. Contributor Workflow for Translations

1. Create a dedicated branch: `docs/i18n-<lang>-<topic>`.
2. Inspect the latest English [`README.md`](../../README.md) for changes.
3. Consult [`TERMINOLOGY.md`](TERMINOLOGY.md) for approved technical vocabulary.
4. Update the target `docs/i18n/README.<lang>.md`.
5. Run automated validation:
   ```bash
   python scripts/ci/validate_i18n.py
   python scripts/ci/validate_docs.py
   ```
6. Open a pull request targeting `main` with prefix `docs(i18n): ...`.
