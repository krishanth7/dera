# Documentation Maintenance Schedule

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Lead Maintainer:** [Krishanth](https://github.com/krishanth7)  
**License:** [MIT License](../../LICENSE)  

---

## 1. Overview & Purpose

Documentation quality degrades over time without structured, recurring maintenance rituals. Technical drift occurs when code evolves, external database documentation links change, or internal architecture diagrams fall behind current abstractions.

This schedule defines the recommended cadence of documentation reviews and audits across three operational intervals:
1. **Per Pull Request** (Continuous, automated & peer review)
2. **Per Release** (Milestone-driven maintainer validation)
3. **Periodic Maintenance** (Quarterly health and freshness reviews)

---

## 2. Maintenance Cadence Matrix

| Activity | Frequency | Trigger | Responsible Party | Verification Method |
|---|---|---|---|---|
| **Technical Accuracy Verification** | Per PR | Any code change altering interfaces or behavior | PR Author & Reviewer | Code review, command execution, tests |
| **Markdown Linting & Link Validation** | Per PR | Any documentation edit | Automated CI | `npm run docs:check`, `validate_docs.py` |
| **Multilingual Parity Check** | Per PR | Edits to root README or translation files | Automated CI | `python scripts/ci/validate_i18n.py` |
| **Release Notes & Changelog** | Per Release | Release candidate or tag creation | Lead Maintainer (`@krishanth7`) | Manual review against merged PR list |
| **Clean Install Verification** | Per Release | Pre-tagging quality gate | Lead Maintainer | Manual execution in clean virtual environment |
| **Database Compatibility Update** | Per Release | Connector dialect qualification | Connector Subsystem Lead | Review against supported DB engine matrix |
| **Translation Freshness Audit** | Per Release | Release candidate tagging | Internationalization Lead | Compare translation matrices against English source |
| **External Link Review** | Quarterly | Scheduled maintainer check | Community Maintainers | Tool-assisted external URL scan (`lychee` / curl) |
| **Diagram & Architecture Audit** | Quarterly | Scheduled maintainer check | Architecture Lead | Visual inspection of Mermaid diagrams vs code |
| **Contributor Onboarding Review** | Biannual | Scheduled maintainer check | Developer Experience Lead | New contributor feedback review |

---

## 3. Detailed Interval Protocols

### 3.1 Per Pull Request (Continuous)
Whenever a pull request is submitted:
1. **Update affected technical documentation:** Verify that code changes (APIs, parameters, connector dialects) have corresponding documentation changes in the same PR.
2. **Validate examples and commands:** Ensure any documented CLI commands, SQL snippets, or API requests are syntactically valid and tested.
3. **Execute local documentation checks:**
   ```bash
   # Run markdownlint, link check, and mermaid validation
   npm run docs:check
   ```
4. **Automated CI Validation:** The `Documentation Quality Gate` and `i18n Navigation Check` GitHub Actions workflows must report a 100% green status before merge.

### 3.2 Per Release (Milestone)
Before publishing an official release (alpha, beta, RC, or stable):
1. **Verify installation instructions:** Run a clean install on a fresh virtual environment following `docs/development/SETUP.md`.
2. **Review release notes:** Ensure all merged pull requests since the last tag are summarized in `CHANGELOG.md` under the appropriate categories.
3. **Update version references:** Synchronize version numbers across package manifests, CLI help text, and documentation headers.
4. **Assess translation freshness:** Identify if any English updates modified the Feature Status Matrix, Database Compatibility, or Quickstart instructions. If so, create follow-up translation tracking issues.
5. **Security disclaimers:** Confirm the strict non-AI policy, read-only database safety invariants, and vulnerability reporting links are intact.

### 3.3 Periodic Maintenance (Quarterly & Biannual)
On a scheduled basis (every 3 to 6 months):
1. **External Link Review:** External links to official database documentation (e.g., PostgreSQL docs, MySQL manual, SQLite docs) should be inspected for dead links or changed URLs.
2. **Diagram Accuracy:** Inspect all Mermaid architecture diagrams in `docs/architecture/` to confirm they reflect actual module imports and dependency graphs.
3. **Audit Stale Documents:** Identify documents that have not been updated in over 6 months using Git history (`git log --stat docs/`). Confirm the content remains accurate or mark it with a Deprecated or Archived banner per the [Documentation Lifecycle Policy](./DOCUMENTATION_LIFECYCLE.md).
4. **Contributor Experience Review:** Review recent contributor issues, questions, and feedback to identify friction points in `CONTRIBUTING.md`, `FIRST_CONTRIBUTION.md`, or developer setup guides.

---

## 4. Current Automation vs. Manual Review

> [!NOTE]
> **Automation Scope Clarification**  
> DERA enforces automated checks **on every pull request** via GitHub Actions:
> - Markdown style compliance (`markdownlint`)
> - Internal link integrity and anchor resolution (`validate_docs.py`)
> - Mermaid diagram syntax validation (`mermaid-cli`)
> - Ten-language navigation and parity validation (`validate_i18n.py`)
>
> Scheduled periodic reviews (e.g., quarterly external link audits, stale document audits, diagram alignment) are performed manually by maintainers and do not rely on scheduled cron bots unless explicitly configured.
