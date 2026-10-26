# DERA Documentation Ownership & Editorial Governance

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:** Krishanth (`krishanth7`)  
> **Parent Guide:** [`docs/governance/MAINTAINERS.md`](MAINTAINERS.md)  
> **Enforcement File:** [`.github/CODEOWNERS`](../../.github/CODEOWNERS)  

---

## 1. Overview & Purpose

As DERA grows, maintaining accurate, high-quality documentation across multiple database dialects, architectural tiers, and ten official languages requires clear ownership lines.

This policy defines the editorial domains, stewardship responsibilities, and review authorities for DERA documentation. It distinguishes between:
1. **GitHub CODEOWNERS:** Enforceable GitHub rules that automatically request approvals on pull requests.
2. **Editorial Stewardship:** Subject-matter domain ownership responsible for technical accuracy, freshness, style conformity, and community alignment.

---

## 2. Documentation Domain Ownership Matrix

| Documentation Domain | Path / Location | Editorial Lead | CODEOWNER | Primary Responsibilities |
|---|---|---|---|---|
| **Root Entrypoint & Identity** | `README.md`, `LICENSE`, `SECURITY.md` | Primary Maintainer | `@krishanth7` | Project mission, non-AI invariants, capability matrix, and security contacts. |
| **System Architecture** | `docs/architecture/` | Systems Architect | `@krishanth7` | Component boundaries, data flow diagrams, monorepo layout, and ADRs. |
| **Database Connectors** | `docs/connectors/` | Connector Lead | `@krishanth7` | Catalog inspection specs, dialect compatibility, read-only safety, and connection security. |
| **Core Domain & Algorithms** | `docs/core/` | Core Engine Lead | `@krishanth7` | Canonical models, graph algorithms, cycle resolution, and diagnostic rules. |
| **Backend & API Gateway** | `docs/backend/`, `apps/api/` | Backend Lead | `@krishanth7` | REST API routes, schemas, loopback binding defaults, and telemetry. |
| **Frontend & Studio Canvas** | `docs/frontend/`, `apps/web/` | Frontend Lead | `@krishanth7` | Web studio architecture, Next.js components, React Flow canvas specs. |
| **Security Architecture** | `docs/security/`, `SECURITY.md` | DevSecOps Lead | `@krishanth7` | Threat models, least-privilege standards, incident disclosure, and security audits. |
| **Developer Guides & CLI** | `docs/development/`, `scripts/` | Developer Experience Lead | `@krishanth7` | Setup instructions, test commands, `dev.py` CLI, and commit guidelines. |
| **Community & Onboarding** | `docs/community/`, `CONTRIBUTING.md` | Community Lead | `@krishanth7` | First-time contributor onboarding, issue triage, Discussions guidance, and FAQ. |
| **Multilingual Translations** | `docs/i18n/` | Internationalization Lead | `@krishanth7` | 10-language synchronization, translation glossaries, and navigation parity. |
| **Roadmap & Releases** | `docs/roadmap/`, `CHANGELOG.md` | Maintainer | `@krishanth7` | 12-phase milestones, versioning, release notes, and breaking changes. |
| **Audit & Baseline Evidence** | `docs/audit/` | Documentation QA Lead | `@krishanth7` | Immutable verification records, baseline audits, test telemetry, acceptance certificates. |

---

## 3. Editorial Stewardship Responsibilities

Editorial domain stewards are responsible for:
1. **Technical Truthfulness:** Ensuring that all claims, diagrams, and instructions reflect actual tested code rather than aspirational features.
2. **Reviewing Domain Pull Requests:** Providing timely, constructive technical feedback on incoming pull requests affecting their domain.
3. **Preventing Documentation Rot:** Periodically reviewing documents for stale commands, outdated dependency references, or dead links.
4. **Guiding Contributors:** Assisting new contributors in authoring clear, well-structured documentation in accordance with the [Documentation Style Guide](../development/DOCUMENTATION_STYLE_GUIDE.md).

---

## 4. Enforceable GitHub CODEOWNERS Rules

All enforceable pull request review assignments are configured in [`.github/CODEOWNERS`](../../.github/CODEOWNERS). Currently, lead maintainer **`@krishanth7`** acts as the primary code owner across all repository paths.

As active contributors demonstrate consistent domain expertise, technical accuracy, and adherence to DERA's deterministic engineering standards, domain-specific code ownership designations may be introduced through an update to `.github/CODEOWNERS`.

---

## 5. How to Report Documentation Issues

- **Factual Inaccuracies or Broken Links:** Open an issue using our [Documentation Issue Form](https://github.com/krishanth7/dera/issues/new?template=documentation.yml).
- **Substantial Rewrites or Structural Additions:** Propose your ideas first in [GitHub Discussions](https://github.com/krishanth7/dera/discussions) under the *Documentation* category.
- **Security Inaccuracies:** Contact `krishanth.b.2008@gmail.com` directly.
