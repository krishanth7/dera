# Contributing Documentation Translations

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:** Krishanth (`krishanth7`)  
> **Parent Policy:** [`docs/i18n/TRANSLATION_POLICY.md`](TRANSLATION_POLICY.md)  
> **Glossary Reference:** [`docs/i18n/TERMINOLOGY.md`](TERMINOLOGY.md)  

---

## 1. Welcome Volunteer Translators! 🌐

Thank you for helping make DERA accessible to software developers and database architects worldwide. DERA officially maintains **exactly ten documentation languages**:

| Language | Code | File Location | Status |
|---|:---:|---|:---:|
| **English** | `en` | [`README.md`](../../README.md), [`docs/i18n/README.en.md`](README.en.md) | **Authoritative Baseline** |
| **Spanish** | `es` | [`docs/i18n/README.es.md`](README.es.md) | Active Translation |
| **French** | `fr` | [`docs/i18n/README.fr.md`](README.fr.md) | Active Translation |
| **German** | `de` | [`docs/i18n/README.de.md`](README.de.md) | Active Translation |
| **Portuguese** | `pt` | [`docs/i18n/README.pt.md`](README.pt.md) | Active Translation |
| **Italian** | `it` | [`docs/i18n/README.it.md`](README.it.md) | Active Translation |
| **Japanese** | `ja` | [`docs/i18n/README.ja.md`](README.ja.md) | Active Translation |
| **Korean** | `ko` | [`docs/i18n/README.ko.md`](README.ko.md) | Active Translation |
| **Simplified Chinese** | `zh-CN` | [`docs/i18n/README.zh-CN.md`](README.zh-CN.md) | Active Translation |
| **Russian** | `ru` | [`docs/i18n/README.ru.md`](README.ru.md) | Active Translation |

> [!IMPORTANT]
> DERA strictly limits documentation to these ten languages. Arabic and Indian regional languages are explicitly excluded from the repository. Please do not submit translations for unapproved languages.

---

## 2. Step-by-Step Translation Workflow

### Step 1: Select Your Language & Issue
1. Check [GitHub Issues](https://github.com/krishanth7/dera/issues?q=is%3Aissue+label%3Ai18n) for open translation tasks or synchronization requests.
2. Comment on the issue to let maintainers know you are working on it.

### Step 2: Compare with Authoritative English Source
1. Open the English [`README.md`](../../README.md).
2. Open the corresponding localized README in `docs/i18n/` (e.g. `docs/i18n/README.es.md`).
3. Identify the sections that require updates or synchronization.

### Step 3: Consult the Terminology Glossary
Review [`docs/i18n/TERMINOLOGY.md`](TERMINOLOGY.md) to ensure consistent technical translations for core concepts:
- *Deterministic* (e.g., Déterministe, Deterministisch, 決定論的, 결정론적, 确定性)
- *Reverse Engineering* (e.g., Rétro-ingénierie, Ingegneria Inversa, リバースエンジニアリング, 역공학, 逆向工程)
- *System Catalogs* (e.g., Catalogues système, Systemkataloge, システムカタログ, 시스템 카탈로그, 系统目录)
- *Schema Snapshot* (e.g., Instantané de schéma, Schema-Snapshot, スキーマスナップショット, 스키마 스냅샷, 模式快照)

### Step 4: Translate Prose & Preserve Technical Code
- **DO translate:** Explanatory text, section headings, table headers, descriptions, and callout notes.
- **DO NOT translate:**
  - Code blocks (`bash`, `python`, `typescript`, `sql`)
  - CLI command flags and commands (`dev.py all`, `npm run docs:check`)
  - Programming identifiers and directory paths (`packages/core`, `Column`, `Table`)
  - Database catalog tables and columns (`sqlite_master`, `pg_catalog`)
  - Mermaid diagram node identifiers (e.g. in `A --> B`, preserve `A` and `B`)

---

## 3. Language-Specific Formatting Guidelines

### UTF-8 Encoding
All translation files must be saved with strict **UTF-8 encoding without BOM** (`DOC-ENC-001`).

### CJK (Chinese, Japanese, Korean) Guidelines
- Use standard full-width punctuation where appropriate (e.g. `。`, `、`, `：` in Chinese and Japanese).
- Maintain appropriate professional technical register:
  - **Japanese:** Polite standard technical style (*desu/masu* form).
  - **Korean:** Formal technical style (*haeyo* or *hapsida* standard).
  - **Simplified Chinese:** Standard contemporary mainland technical prose.
- When inserting Latin words or code terms into CJK sentences, include a single half-width space before and after the Latin term for enhanced readability.

### Russian / Cyrillic Guidelines
- Ensure headings containing Cyrillic characters generate valid GitHub anchor links.
- Maintain standard database engineering terms (e.g., *обратная инженерия*, *системные каталоги*, *инвариант детерминизма*).

---

## 4. Preserving Managed Navigation Markers

All localized README files begin with a managed navigation block bounded by HTML comments:

```markdown
<!-- DERA:I18N_NAV:START -->
...
<!-- DERA:I18N_NAV:END -->
```

**Do not manually edit the text inside these markers.**  
Navigation is automatically maintained by our deterministic generator:
```bash
python scripts/docs/generate_language_navigation.py --write
```

---

## 5. Validating Your Translation Locally

Before opening a pull request, verify that your changes pass automated quality gates:

```bash
# 1. Validate translation manifest and navigation
npm run docs:i18n

# 2. Run full documentation checks (linting, links, mermaid)
npm run docs:check
```

Both commands must report **SUCCESS** with exit code 0.

---

## 6. Submitting Your Translation PR

1. Commit your changes following [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "docs(i18n): update Japanese README feature matrix"
   ```
2. Open a Pull Request referencing the related issue.
3. Our internationalization team will review your contribution for quality, formatting, and technical accuracy.
