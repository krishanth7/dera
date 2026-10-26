# Frequently Asked Questions for Contributors (FAQ)

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:** Krishanth (`krishanth7`)  
> **Parent Guide:** [`CONTRIBUTING.md`](../../CONTRIBUTING.md)  

---

## 1. Getting Started & Task Selection

### Q: I am new to DERA. Where should I start?
**A:** Start with our [First Contribution Guide](FIRST_CONTRIBUTION.md). Browse issues labeled [**`good first issue`**](https://github.com/krishanth7/dera/labels/good%20first%20issue) or [**`documentation`**](https://github.com/krishanth7/dera/labels/documentation). Check our [Contribution Areas](CONTRIBUTION_AREAS.md) map to match your skills with current project needs.

### Q: Which branch should I base my work on?
**A:** Always branch off the latest default branch: `main`. Keep your personal fork synchronized with `upstream/main` before opening a branch. Use the appropriate branch prefix:
- `feat/` for new features
- `fix/` for bug fixes
- `docs/` for documentation
- `test/` for testing improvements
- `refactor/` for internal cleanup

---

## 2. Issues & Feature Proposals

### Q: How do I report a bug?
**A:** Open an issue using our [Bug Report Form](https://github.com/krishanth7/dera/issues/new?template=bug_report.yml). Provide a minimal reproducible example, your operating system, Python/Node versions, and database engine. **Never include real database passwords or connection secrets.**

### Q: How do I propose a new feature or database connector?
**A:** For substantial new capabilities or architectural shifts, start an open topic in [GitHub Discussions](https://github.com/krishanth7/dera/discussions) under the *Ideas* or *Architecture* category. Once aligned with the maintainer, submit a [Feature Request Form](https://github.com/krishanth7/dera/issues/new?template=feature_request.yml).

---

## 3. Documentation & Translations

### Q: How do I contribute a documentation improvement?
**A:** For small typo fixes or clarifications, you can edit directly on GitHub via the web interface (click the pencil icon ✏️ on any file). For larger additions, follow our [Documentation Style Guide](../development/DOCUMENTATION_STYLE_GUIDE.md) and run `npm run docs:check` locally before submitting your pull request.

### Q: How do I help translate documentation?
**A:** DERA officially maintains **exactly ten languages**: `en`, `es`, `fr`, `de`, `pt`, `it`, `ja`, `ko`, `zh-CN`, `ru`. Read our [Translating Documentation Guide](../i18n/CONTRIBUTING_TRANSLATIONS.md) for glossary standards and UTF-8 instructions. Do not translate code blocks, SQL snippets, or programming variables.

---

## 4. Development & Testing

### Q: Which local tests must I run before opening a pull request?
**A:** You can verify everything locally with a single command:
```bash
python scripts/development/dev.py all
```
This runs:
1. Python compile checks
2. Python unit & integration test suites
3. TypeScript compiler static typecheck (`tsc --noEmit`)
4. Documentation quality gate (`npm run docs:check`)

For documentation-only pull requests, you can run:
```bash
npm run docs:check
```

### Q: What should I do if a GitHub Actions CI check fails?
**A:**
1. Click **Details** next to the failing check in your pull request.
2. Read the log message. If it is a documentation issue, look for the file and line number (e.g. `DOC-ANCH-004` or `MD040`).
3. Reproduce the failure locally:
   - For doc errors: `npm run docs:check`
   - For Python test failures: `python scripts/development/dev.py test`
   - For type errors: `python scripts/development/dev.py typecheck`
4. Commit your fix to your feature branch and push to your fork. GitHub Actions will automatically re-run.

---

## 5. Security & Review Policies

### Q: How do I report a security vulnerability?
**A:** **Do not open a public GitHub issue.** Privately report security concerns via:
- [GitHub Private Vulnerability Reporting](https://github.com/krishanth7/dera/security/advisories/new)
- Direct security contact: `krishanth.b.2008@gmail.com`  
See our [Root Security Policy](../../SECURITY.md) and [Vulnerability Response Guide](../security/VULNERABILITY_RESPONSE.md).

### Q: How are pull requests reviewed and merged?
**A:** The repository maintainer reviews all pull requests according to our [Code Review Policy](../development/CODE_REVIEW_POLICY.md) and [Documentation Review Policy](../governance/DOCUMENTATION_REVIEW_POLICY.md). All required CI checks must pass. PRs are integrated using GitHub squash-and-merge to preserve a clean, linear Git history.
