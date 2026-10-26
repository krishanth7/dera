<!-- DERA:I18N_NAV:START -->
[English](../README.md) | [Español](i18n/README.es.md) | [Français](i18n/README.fr.md) | [Deutsch](i18n/README.de.md) | [Português](i18n/README.pt.md) | [Italiano](i18n/README.it.md) | [日本語](i18n/README.ja.md) | [한국어](i18n/README.ko.md) | [简体中文](i18n/README.zh-CN.md) | [Русский](i18n/README.ru.md)
<!-- DERA:I18N_NAV:END -->

---

# DERA Documentation Index

Welcome to the official technical documentation for **DERA — Database Engineering & Reverse Analysis**.

**Tagline:** Understand Every Schema. Engineer Every Change.  
**Maintainer:** Krishanth  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**License:** [MIT License](../LICENSE)  
**Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 📚 Technical Documentation Hubs

| Hub | Description | Primary Reference |
|---|---|---|
| **System Architecture** | Architectural philosophy, component diagrams, monorepo structure, and data flows | [docs/architecture/SYSTEM_OVERVIEW.md](architecture/SYSTEM_OVERVIEW.md) |
| **Backend Gateway** | FastAPI application structure, security middleware, and verified REST API contracts | [docs/backend/APPLICATION_ARCHITECTURE.md](backend/APPLICATION_ARCHITECTURE.md) |
| **Frontend Studio** | Next.js 15 studio scaffold, component hierarchy, and typed API client | [docs/frontend/APPLICATION_ARCHITECTURE.md](frontend/APPLICATION_ARCHITECTURE.md) |
| **Deterministic Core** | Pure Python canonical domain models, Kahn DAG algorithms, and rule diagnostics | [docs/core/README.md](core/README.md) |
| **Database Connectors** | Read-only connection lifecycle, query mutation safety, and capability matrix | [docs/connectors/CONNECTOR_ARCHITECTURE.md](connectors/CONNECTOR_ARCHITECTURE.md) |
| **Shared Contracts** | JSON Schema exchange specifications and TypeScript protocol definitions | [docs/contracts/SCHEMA_CONTRACTS.md](contracts/SCHEMA_CONTRACTS.md) |
| **Getting Started & Setup** | Quickstart onboarding, prerequisites, and developer environment setup | [docs/development/GETTING_STARTED.md](development/GETTING_STARTED.md) |
| **Developer Workflow** | CLI commands reference, branching strategy, Conventional Commits, and PR lifecycle | [docs/development/CONTRIBUTION_WORKFLOW.md](development/CONTRIBUTION_WORKFLOW.md) |
| **Testing & Quality Gates** | Python unit tests, TypeScript type checks, and architecture invariants | [docs/development/TESTING.md](development/TESTING.md) |
| **Security Architecture** | Threat modeling, read-only guarantees, credential safety, and vulnerability triage | [docs/security/SECURITY_ARCHITECTURE.md](security/SECURITY_ARCHITECTURE.md) |
| **Community & Contributing** | First contribution walkthrough, contribution categories, and contributor FAQ | [docs/community/README.md](community/README.md) |
| **Documentation Governance** | Ownership, review standards, style guide, release docs, and lifecycle policies | [docs/governance/README.md](governance/README.md) |
| **International Documentation** | 10-language translations, translation maintenance, and translation guides | [docs/i18n/README.en.md](i18n/README.en.md) |
| **Audit & Baseline Reports** | Phase audit reports, baseline assessments, and acceptance certificates | [docs/audit/README.md](audit/README.md) |
| **Roadmap & Milestones** | Master 12-Phase development roadmap and engineering delivery schedule | [docs/roadmap/README.md](roadmap/README.md) |

---

## 🌍 Multilingual README Directory (`docs/i18n/`)

DERA maintains synchronized documentation in 10 international languages:

- 🇬🇧 **English:** [Root README](../README.md) · [Synchronized Copy](i18n/README.en.md)
- 🇪🇸 **Español:** [Spanish Documentation](i18n/README.es.md)
- 🇫🇷 **Français:** [French Documentation](i18n/README.fr.md)
- 🇩🇪 **Deutsch:** [German Documentation](i18n/README.de.md)
- 🇵🇹 **Português:** [Portuguese Documentation](i18n/README.pt.md)
- 🇮🇹 **Italiano:** [Italian Documentation](i18n/README.it.md)
- 🇯🇵 **日本語:** [Japanese Documentation](i18n/README.ja.md)
- 🇰🇷 **한국어:** [Korean Documentation](i18n/README.ko.md)
- 🇨🇳 **简体中文:** [Simplified Chinese Documentation](i18n/README.zh-CN.md)
- 🇷🇺 **Русский:** [Russian Documentation](i18n/README.ru.md)

---

## 🎯 Technical Principles

1. **Deterministic by Design:** Every schema snapshot, graph resolution, and diagnostic report is reproducible and rule-based.
2. **Strictly Non-AI:** DERA contains no machine learning, generative AI, LLMs, or external AI inference dependencies.
3. **Metadata-First & Privacy:** Analysis examines database system catalogs (`information_schema`, `sqlite_master`). Customer data rows are never extracted by default.
4. **Least Privilege & Read-Only:** Database operations enforce read-only execution at the connection level.

---

For contribution guidelines, refer to [CONTRIBUTING.md](../CONTRIBUTING.md). For security reports, consult [SECURITY.md](../SECURITY.md).
