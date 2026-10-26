# DERA Technical Documentation Guidelines & Standards

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Maintainer:** Krishanth ([@krishanth7](https://github.com/krishanth7))  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Scope:** Authoring, validating, and formatting technical documentation  

---

## 1. Documentation Philosophy & Purpose

Documentation in DERA is treated with the same engineering rigor as production code:
- **Accuracy over Aspiration:** Never present planned features as implemented. Clearly distinguish between **Implemented**, **Experimental**, and **Planned** capabilities.
- **Evidence-Based Content:** Claims regarding performance, security, and schema analysis must cite concrete code, algorithms, or tests.
- **Strictly Non-AI:** Do not use vague or hallucinated promotional language. Use precise, unambiguous database engineering terminology.
- **Cross-Platform Reproducibility:** Ensure documented commands are executable on Windows, Linux, and macOS.

---

## 2. Markdown & Structural Formatting Rules

All documentation files in `docs/` and localized translations must adhere to strict structural constraints:

1. **Top-Level H1 Heading:** Every markdown document must begin with exactly one top-level `# Heading 1`.
2. **Deterministic Heading Hierarchy:** Headings must follow descending levels (`#` -> `##` -> `###`) without skipping levels.
3. **Relative File Links:** Use relative paths (e.g., `[Overview](../architecture/overview.md)`), never hardcoded local machine paths.
4. **Exact Case Matching:** File links must match disk filenames with exact case sensitivity to avoid broken links on Linux CI runners.
5. **UTF-8 Encoding:** All files must be saved with UTF-8 encoding without Byte Order Marks (BOM).
6. **Code Blocks:** Fenced code blocks must always declare an explicit language identifier (`bash`, `python`, `typescript`, `sql`, `json`, `text`, `mermaid`).

---

## 3. Mermaid Diagram Conventions

Architecture and lifecycle diagrams should use GitHub-compatible Mermaid blocks:
- **Diagram Types:** Prefer `flowchart TD`/`LR`, `sequenceDiagram`, and `gitGraph`.
- **Node Escaping:** Wrap labels containing parentheses or symbols in double quotes: `ID["Node (Context)"]`.
- **No Raw HTML in Labels:** Avoid raw HTML tags (`<br/>`, `<b>`) inside node labels unless fully supported.
- **Theme Readability:** Diagrams must render legibly across both GitHub light and dark themes.

---

## 4. Multilingual Documentation Standards

DERA maintains documentation in 10 international languages (`docs/i18n/`):

| Language | Code | File | Formatting Guidance |
|---|---|---|---|
| English | `en` | `docs/i18n/README.en.md` | Authoritative technical reference |
| Spanish | `es` | `docs/i18n/README.es.md` | Full translation, keep code blocks untranslated |
| French | `fr` | `docs/i18n/README.fr.md` | Full translation, preserve technical terms |
| German | `de` | `docs/i18n/README.de.md` | Full translation, maintain compound terms |
| Portuguese | `pt` | `docs/i18n/README.pt.md` | Full translation, consistent database terms |
| Italian | `it` | `docs/i18n/README.it.md` | Full translation, standard database terms |
| Japanese | `ja` | `docs/i18n/README.ja.md` | Full translation, preserve ASCII symbols |
| Korean | `ko` | `docs/i18n/README.ko.md` | Full translation, standard IT terminology |
| Simplified Chinese | `zh-CN` | `docs/i18n/README.zh-CN.md` | Full translation, standard Chinese database terms |
| Russian | `ru` | `docs/i18n/README.ru.md` | Full translation, Cyrillic typography |

**Translation Rules:**
- Keep code identifiers, SQL queries, file paths, and environment variable names untranslated.
- Preserve identical relative file links across all language READMEs.
- Strictly adhere to [`docs/i18n/TERMINOLOGY.md`](../i18n/TERMINOLOGY.md) for technical terms.

---

## 5. Automated Validation Commands

Before committing any documentation changes, run our automated CI validation suite:

```bash
# Validate internal markdown links and heading hierarchies
python scripts/ci/validate_docs.py

# Validate 10-language international navigation parity
python scripts/ci/validate_i18n.py

# Run all baseline checks
python scripts/development/dev.py all
```
