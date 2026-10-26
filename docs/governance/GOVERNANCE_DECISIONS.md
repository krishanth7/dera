# Governance & Architectural Decision Records (GAD)

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Lead Maintainer:** [Krishanth](https://github.com/krishanth7)  
**Status:** Living Document  

---

## Overview

This document records key foundational governance and architectural policy decisions for DERA. Each record details context, decision, rationale, and consequences.

---

## GAD-001: MIT Open Source Licensing

- **Date:** October 2026
- **Status:** Accepted
- **Context:** DERA requires a clear, permissive, and universally recognized open-source licensing model that encourages broad adoption by database administrators, platform developers, and organizations.
- **Decision:** Adopt the standard [MIT License](../../LICENSE) with copyright held by `Krishanth`.
- **Consequences:** All inbound contributions must be licensed under the MIT License without additional restrictive conditions. Third-party dependencies must remain strictly compatible with MIT (permissive licenses only).

---

## GAD-002: Strictly Deterministic Non-AI Runtime Mandate

- **Date:** October 2026
- **Status:** Accepted
- **Context:** Database reverse engineering, relationship discovery, and migration safety require 100% reproducible, verifiable, and audit-compliant outcomes. Non-deterministic generative AI models introduce hallucinations, unpredictable schema alterations, and third-party data transmission risks.
- **Decision:** Mandate that DERA core packages, connectors, and analysis engines remain strictly deterministic. Prohibit all runtime dependencies on external AI inference APIs (OpenAI, Anthropic, Google Gemini, Groq) or local LLM execution runtimes.
- **Consequences:** All schema extraction, foreign-key inference, graph topology, and SQL diagnostics must rely exclusively on deterministic algorithms (catalog queries, graph theory, AST parsing, static rules).

---

## GAD-003: Read-Only Database Safety & Zero Row Extraction

- **Date:** October 2026
- **Status:** Accepted
- **Context:** Connecting reverse-engineering tools to production or enterprise databases introduces operational risks of accidental mutation, service degradation, or sensitive data leakage.
- **Decision:** Mandate a metadata-first architecture:
  1. DERA connects using database accounts restricted to read-only catalog access.
  2. Transaction sessions are explicitly set to read-only mode (`SET TRANSACTION READ ONLY`).
  3. Static query inspection blocks destructive SQL statements (`DROP`, `TRUNCATE`, `ALTER`, `INSERT`, `UPDATE`, `DELETE`, `GRANT`, `REVOKE`).
  4. Inspection routines query system catalogs exclusively; DERA never executes `SELECT *` against customer application tables.
- **Consequences:** User confidence and compliance posture are dramatically improved; destructive accidental schema modifications are technically intercepted.

---

## GAD-004: Maintainer-Led Governance for Phase 1

- **Date:** October 2026
- **Status:** Accepted
- **Context:** At the initial repository foundation phase, swift decision-making, architectural consistency, and tight security oversight are vital.
- **Decision:** Establish a maintainer-led stewardship model with [@krishanth7](https://github.com/krishanth7) as Lead Maintainer and designated code owner across all components.
- **Consequences:** Clear accountability for code quality and security. Establishes a predictable escalation path. Lays out a clear transition mechanism to community steering committees in future development phases.

---

## GAD-005: GitHub Private Vulnerability Reporting

- **Date:** October 2026
- **Status:** Accepted
- **Context:** Security researchers require a confidential mechanism to report potential vulnerabilities without exposing sensitive details on public GitHub issues.
- **Decision:** Adopt GitHub Private Vulnerability Reporting as the primary intake channel (`/security/advisories/new`), supplemented by a direct maintainer email (`krishanth.b.2008@gmail.com`).
- **Consequences:** Public bug templates explicitly warn against posting secrets or security flaws; private advisories allow coordinated disclosure and CVE tracking if applicable.

---

## GAD-006: Conventional Commits 1.0.0 & Squash-Merge Lifecycle

- **Date:** October 2026
- **Status:** Accepted
- **Context:** Clear changelogs, automated semantic versioning, and traceable Git history are essential for enterprise open-source software.
- **Decision:** Enforce Conventional Commits 1.0.0 on all commit messages and pull request titles. Require squash-merging of pull requests into `main` with 100% CI status check passage.
- **Consequences:** CI workflows validate PR titles automatically; Git history remains linear, clean, and easily auditable.

---

## GAD-007: 10-Language Internationalization Framework

- **Date:** October 2026
- **Status:** Accepted
- **Context:** Database reverse engineering is a global challenge across multilingual developer communities.
- **Decision:** Establish a 10-language internationalization framework (`en`, `es`, `fr`, `de`, `pt`, `ja`, `ko`, `zh-CN`, `ar`, `ru`) with dedicated documentation in `docs/i18n/`.
- **Consequences:** International users can navigate and understand project capabilities in their native language; English serves as the authoritative technical reference.
