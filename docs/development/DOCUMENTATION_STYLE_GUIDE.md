# DERA Documentation Style Guide

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:** Krishanth (`krishanth7`)  
> **Standard:** Professional, evidence-based, accessible, deterministic  

---

## 1. Purpose & Guiding Principles

Clear, accurate, and consistent technical documentation is essential for DERA's mission. This style guide establishes rules for all technical documentation, architectural specifications, contributor tutorials, and translations.

### Foundational Principles
1. **Truth-in-Documentation:** Always distinguish currently implemented and tested capabilities from planned roadmap milestones. Never claim a feature is "production-ready" or "fully automated" unless verified by automated test fixtures in CI.
2. **Deterministic & Non-AI:** DERA documentation must never promote, describe, or assume generative AI, LLM inference, or probabilistic mechanisms within DERA core operations.
3. **Concise & Actionable:** Respect the reader's time. Use direct, clear technical language with verified code examples.
4. **Accessible by Default:** Ensure all visual diagrams have accompanying text breakdowns, headings increment logically, and color is never used as the sole indicator of status.

---

## 2. Structure & Heading Hierarchy

- **Single H1 per document:** Every Markdown document must start with exactly one `# Level 1 Heading`.
- **Sequential Increments:** Never skip heading levels (e.g. do not jump directly from `# Title` to `### Subsection` without an intervening `## Section`).
- **Heading Casing:** Use Title Case for H1 and H2 headings (`## 2. Architecture Overview`), and sentence case or Title Case for H3/H4 subheadings.
- **No Trailing Punctuation:** Headings must not end with a colon `:`, period `.`, or semicolon `;` (enforced by markdownlint `MD026`).
- **Emojis in Headings:** If an emoji is used in a major section heading (e.g. `## 🏗️ Architecture Overview`), ensure cross-references use compatible GitHub anchor slugs (`#️-architecture-overview` or `#-architecture-overview`).

---

## 3. Markdown Formatting Standards

DERA enforces Markdown rules via `.markdownlint-cli2.jsonc`.

- **Trailing Whitespace:** Lines must not contain trailing spaces (`MD009`), except where two spaces explicitly indicate a line break in Markdown blocks.
- **Consecutive Blank Lines:** Use at most one blank line between paragraphs, headings, or list items (`MD012`).
- **Lists:**
  - Surround lists with blank lines (`MD032`).
  - Use `-` for unordered list items.
  - Keep list indentation consistent (2 or 4 spaces).
- **Tables:**
  - Surround tables with blank lines above and below (`MD058`).
  - Every row in a table must have the exact same number of pipe delimiters as the header row (`MD056`).
  - Escape pipes inside table code spans (e.g., use `\|` rather than `|`).

---

## 4. Code Blocks & Fences

- **Always Specify Language Identifiers (`MD040`):** Every fenced code block must declare a valid language identifier.
  - Shell / CLI: ```` ```bash ```` or ```` ```sh ````
  - Python: ```` ```python ````
  - TypeScript / JavaScript: ```` ```typescript ```` / ```` ```javascript ````
  - SQL: ```` ```sql ````
  - JSON / YAML: ```` ```json ```` / ```` ```yaml ````
  - Plain Text / ASCII Diagrams: ```` ```text ````
  - Diagrams: ```` ```mermaid ````
- **Syntax Validity:** JSON blocks marked `json` and YAML blocks marked `yaml` are automatically syntax-checked during doc validation (`DOC-CODE-006`). Ensure they contain valid JSON/YAML.
- **No Real Secrets:** Never include real database passwords, production connection URIs, or private API keys in examples. Always use placeholders like `STRONG_RANDOMLY_GENERATED_PASSWORD` or `127.0.0.1:5432/test_db`.

---

## 5. Visual Diagrams (Mermaid)

- **Use Native Mermaid:** Prefer fenced ````mermaid```` blocks over static images for architecture and flow diagrams.
- **Balanced Syntax:**
  - Every `subgraph` in a flowchart or `loop/alt/opt` in a sequence diagram must have a matching `end`.
  - Node labels containing parentheses, brackets, or special characters must be enclosed in double quotes: `NODE["Label (Extra Details)"]`.
- **Textual Fallback:** For complex architectural diagrams, provide an accessible text summary directly beneath the diagram to assist screen-reader users.

---

## 6. Hyperlinks & Cross-References

- **Exact Relative Paths:** Link directly to the target file (e.g. `[Core Models](../../packages/core/src/dera/models.py)`).
- **Case Sensitivity:** File and directory names are verified with strict case sensitivity (`DOC-CASE-005`). Match the exact disk casing (e.g. `README.md`, not `readme.md`).
- **Heading Anchors:** Validate that any anchor fragment (`#heading-slug`) matches a real heading in the target document (`DOC-ANCH-004`).
- **External Links:** Keep external links minimal and reputable. External links are validated in a weekly scheduled job (`.github/workflows/external-links.yml`).

---

## 7. Terminology & Tone Standards

| Approved Term | Disapproved / Deprecated Term | Rationale |
|---|---|---|
| **Deterministic** | "AI-powered", "Smart", "Predictive" | DERA is strictly non-AI and non-probabilistic. |
| **System Catalog** | "Data tables", "User records" | DERA inspects database metadata only, never customer row data. |
| **Read-Only Inspection** | "Database scanner", "Scraper" | Emphasizes read-only safety and transactional isolation. |
| **Monorepo** | "Multi-repo", "Collection of tools" | DERA is an integrated modular monorepo. |
| **Planned (Roadmap Phase X)** | "Coming soon", "Beta" (if not implemented) | Clear, transparent roadmap status. |

---

## 8. Security Callouts & Alerts

Use GitHub Markdown blockquotes with alerts for important technical, safety, or security warnings:

```markdown
> [!IMPORTANT]
> DERA connects to databases using read-only credentials with minimal catalog permissions.

> [!WARNING]
> Never execute DDL or administrative commands against production databases during manual testing.
```

---

## 9. Local Style Validation

Validate your documentation locally before opening a pull request:

```bash
# Run markdownlint across all docs
npm run docs:lint

# Run full documentation quality gate (lint, links, mermaid, navigation)
npm run docs:check
```
