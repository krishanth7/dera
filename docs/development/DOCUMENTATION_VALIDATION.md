# DERA Documentation Validation & Quality Gates Guide

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Documentation Standard:** Deterministic, reliable, secure, multilingual  

---

## 1. Overview & Objectives

High-quality, reliable technical documentation is a first-class engineering priority for DERA. Because DERA serves enterprise database architects and developers globally, documentation errors—such as broken internal references, invalid Mermaid diagrams, unclosed code fences, or misaligned translations—compromise project integrity and developer experience.

DERA enforces a **layered, deterministic documentation quality system** integrated into both local developer workflows and automated GitHub Actions pull request gates.

```text
[Documentation Markdown Sources (*.md)]
              │
              ├─► Layer 1: Markdown Linting (markdownlint-cli2)
              │            └── Fenced code blocks, headings, trailing spaces, clean Markdown
              │
              ├─► Layer 2: Internal Link & Anchor Integrity (validate_docs.py)
              │            └── Exact target existence, GitHub anchor resolution, case sensitivity
              │
              ├─► Layer 3: Mermaid Diagram Syntax Validation (validate_mermaid.py)
              │            └── Diagram type verification, balanced subgraphs, quotes & brackets
              │
              ├─► Layer 4: Multilingual Parity & Navigation (validate_i18n.py)
              │            └── Exactly 10 official languages, manifest ordering, active indicators, token preservation
              │
              ├─► Layer 5: Technical Consistency & Structure Checks (validate_docs.py)
              │            └── Mandatory entry points, pyproject.toml Python requirements parity
              │
              └─► Layer 6: Isolated External Link Health Check (validate_external_links.py)
                           └── Weekly scheduled health check; strictly decoupled from PR blocks
```

---

## 2. Local Validation Commands

Contributors can run individual checks or the entire validation suite locally using npm scripts or the Python development runner (`dev.py`).

| Command | Tool / Script | Scope & Description | Network Required |
|---|---|---|:---:|
| `npm run docs:lint` | `markdownlint-cli2` | Scans all documentation for Markdown style rules, code fences, and heading syntax. | **No (Offline)** |
| `npm run docs:links` | `scripts/ci/validate_docs.py` | Validates internal file links, GitHub heading anchors, case sensitivity, and entry points. | **No (Offline)** |
| `npm run docs:mermaid` | `scripts/ci/validate_mermaid.py` | Scans and validates syntax for all fenced Mermaid diagrams across documentation. | **No (Offline)** |
| `npm run docs:i18n` | `scripts/ci/validate_i18n.py` | Verifies canonical 10-language manifest, language order, code block parity, and token preservation. | **No (Offline)** |
| `npm run docs:check` | Composite | Executes all deterministic checks (linting, links, mermaid, navigation, i18n parity) in sequence. | **No (Offline)** |
| `python scripts/development/dev.py validate-docs` | `dev.py` | Unified cross-platform CLI executing linting, links, mermaid, and navigation checks. | **No (Offline)** |
| `npm run docs:links:external` | `scripts/ci/validate_external_links.py` | Validates external HTTP/HTTPS links with timeouts, retries, and documented exclusions. | **Yes (Online)** |

---

## 3. How to Fix Validation Issues

### 3.1 Markdown Linting Errors (`markdownlint-cli2`)

DERA uses `.markdownlint-cli2.jsonc` to enforce clean Markdown structure while permitting justified exceptions for long technical URLs, tables, badges, and multilingual templates.

Common errors:
- **`MD040/fenced-code-language`**: Fenced code blocks must have a language tag specified (e.g., ```` ```text ````, ```` ```sql ````, ```` ```bash ````, ```` ```python ````).
- **`MD009/no-trailing-spaces`**: Lines must not end with unintended whitespace. Remove trailing spaces at line ends.
- **`MD026/no-trailing-punctuation`**: Headings should not end in colons or trailing punctuation (e.g. use `## 2. Setup` instead of `## 2. Setup:`).
- **`MD056/table-column-count`**: Table rows must have the exact same number of columns as the header row. Be careful not to use unescaped pipes (`\|`) inside table code spans.

### 3.2 Broken Internal Links (`DOC-LINK-003`, `DOC-CASE-005`)

- **Missing File (`DOC-LINK-003`)**: Ensure the relative path points to an existing file or directory. For example, from `docs/development/TESTING.md`, link to architecture docs via `../architecture/README.md`.
- **Case Mismatch (`DOC-CASE-005`)**: On case-insensitive filesystems (Windows/macOS), referencing `docs/readme.md` instead of `docs/README.md` passes locally but fails on Linux GitHub Actions runners. Always use exact on-disk casing.

### 3.3 Broken Heading Anchors (`DOC-ANCH-004`)

When linking to a section in a document (e.g. `[Overview](#1-overview)`):
1. **GitHub Heading Slugs**: GitHub converts headings to lowercase, removes punctuation (`!`, `@`, `#`, `$`, `%`, `&`, `*`, `(`, `)`, `:`, etc.), and replaces spaces with hyphens.
2. **Emoji Headings**: When linking to headings with leading emojis (e.g. `## 🏗️ Architecture Overview`), GitHub strips the emoji and leaves a leading hyphen from the space (e.g. `#-architecture-overview` or `architecture-overview`). Both formats are accepted by DERA's validator.
3. **Duplicate Headings**: If a document has duplicate headings, GitHub appends `-1`, `-2`, etc. to subsequent occurrences.

### 3.4 Mermaid Diagram Syntax Errors (`MERMAID-001` - `MERMAID-005`)

- **`MERMAID-001` (Unknown diagram type)**: The first non-comment line must declare a recognized diagram type (e.g. `flowchart TD`, `graph TD`, `sequenceDiagram`, `gantt`).
- **`MERMAID-002` (Unbalanced subgraph / block)**: Every `subgraph` in a flowchart or `loop/alt/opt` in a sequence diagram must have a matching `end`.
- **`MERMAID-003` (Unbalanced quotes / brackets)**: Ensure double quotes inside node labels are balanced. Node labels with special characters should be enclosed in quotes: `NODE["Label (Extra Info)"]`.

### 3.5 Updating Multilingual Navigation & Translations

Whenever a new document is added to the 10-language managed navigation targets:
1. Ensure the language is defined in [`docs/i18n/languages.json`](../i18n/languages.json).
2. Run the navigation generator in write mode:
   ```bash
   python scripts/docs/generate_language_navigation.py --write
   ```
3. Run the internationalization validator:
   ```bash
   python scripts/ci/validate_i18n.py
   ```
4. Verify non-translatable technical tokens (`packages/core`, `apps/api`, etc.) and code fence sequence parity:
   ```bash
   python -m unittest tests/docs/test_i18n_parity.py
   ```

---

## 4. External Link Policy & Exclusions

External links are validated in an **isolated, scheduled workflow** (`.github/workflows/external-links.yml`) running weekly on Mondays at 04:00 UTC. External network checks are decoupled from pull request quality gates so that third-party website downtime does not block feature pull requests.

### Documented Exclusions (`.lychee.toml` & `validate_external_links.py`)

All exclusions are narrowly scoped and require an explicit technical rationale:
1. `https://github.com/krishanth7/dera/security/advisories/new`: Requires authenticated GitHub login to view the private security advisory creation form.
2. `https://img.shields.io/*`: Dynamic badge generation endpoint that frequently rate-limits automated HEAD requests.
3. `https?://example.com*`: RFC 2606 reserved domain used exclusively for illustrative documentation examples.
4. `https?://127.0.0.1*` and `https?://localhost*`: Local loopback addresses used in technical documentation code examples.

---

## 5. Interpreting CI Failures

DERA executes two consolidated, non-overlapping documentation workflows:

```text
1. DERA | Documentation Validation
   ├── 1. Markdown Linting (markdownlint-cli2) .............. PASS
   ├── 2. Internal Link, Anchor & Structure Validation ..... PASS
   ├── 3. Mermaid Diagram Syntax Validation ................ PASS
   └── 4. Documentation Quality Regression Tests ........... PASS

2. DERA | Multilingual Validation
   ├── 1. Navigation Synchronization (--check) ............. PASS
   ├── 2. Translation Parity & Token Verification .......... PASS
   └── 3. Multilingual & Parity Regression Tests ........... PASS
```

If a step fails, the log output includes the exact file path, line number, stable error code, and remediation guidance:
```text
docs/architecture/DATA_FLOW.md:64: ERROR DOC-ANCH-004: Anchor '#catalog-inspection' not found in target file 'README.md'
```

Resolve the diagnostic issue locally with `npm run docs:check` before pushing your update.
