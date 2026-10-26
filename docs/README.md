# DERA Documentation Index

Welcome to the official technical documentation for **DERA — Database Engineering & Reverse Analysis**.

**Tagline:** Understand Every Schema. Engineer Every Change.  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**License:** [MIT License](../LICENSE)

---

## 📚 Documentation Sections

| Section | Description | Link |
|---|---|---|
| **Architecture** | System components, data pipelines, deterministic processing engine, and database connectors | [docs/architecture/overview.md](architecture/overview.md) |
| **Development** | Local development environment, coding standards, tooling, and testing strategy | [docs/development/setup.md](development/setup.md) |
| **Documentation Lifecycle** | English source-of-truth policy, truth-in-documentation, and PR doc standards | [docs/development/README_MAINTENANCE.md](development/README_MAINTENANCE.md) |
| **Security** | Threat modeling, credential encryption, read-only guarantees, SSRF defense, and audit logging | [docs/security/model.md](security/model.md) |
| **Contributing** | Contribution guidelines, connector development, and code review criteria | [docs/contributing/guide.md](contributing/guide.md) |
| **Governance** | Project stewardship, code owners, decision records, and third-party license inventory | [docs/governance/README.md](governance/README.md) |
| **Roadmap** | Master 12-Phase development roadmap, milestone targets, and delivery timeline | [docs/roadmap/README.md](roadmap/README.md) |
| **Audit & Baseline** | Repository audit reports, risk registers, and Phase 1 completion evidence | [docs/audit/README.md](audit/README.md) |
| **Multilingual Documentation** | Complete synchronized documentation in 10 international languages | [docs/i18n/](i18n/README.en.md) |

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
3. **Metadata-First & Privacy:** Analysis examines database system catalogs (`information_schema`, `pg_catalog`). Customer data rows are never extracted by default.
4. **Least Privilege & Read-Only:** Database operations enforce read-only execution at the connection level.

---

For contribution guidelines, refer to [CONTRIBUTING.md](../CONTRIBUTING.md). For security reports, consult [SECURITY.md](../SECURITY.md).
