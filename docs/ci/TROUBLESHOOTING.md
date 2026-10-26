# DERA CI/CD Troubleshooting & Diagnostic Guide

This guide helps contributors and maintainers quickly diagnose and resolve failing GitHub Actions checks.

---

## 1. Common Failures & Remediation

### Failure 1: PR Title Fails (`DERA | PR Title Validator`)
* **Error:** `ERROR: Pull request title violates Conventional Commits format.`
* **Cause:** The PR title does not follow the `<type>(<optional-scope>): <summary>` format.
* **Remediation:**
  * Edit the PR title in the GitHub UI.
  * Valid types: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`, `security`.
  * Examples:
    * `feat(connector): add PostgreSQL catalog inspection`
    * `fix(schema): handle composite foreign keys`
    * `docs(i18n): update Japanese README`

---

### Failure 2: PR Readiness Check Fails (`DERA | PR Readiness`)
* **Error:** `PR Readiness Validation FAILED: PR description is too short...`
* **Cause:** The pull request body is missing a description of changes or test instructions.
* **Remediation:**
  * Edit the PR body to include a **Summary** section, a **Testing** explanation, or check off the checklist items from `.github/PULL_REQUEST_TEMPLATE.md`.

---

### Failure 3: Documentation Validation Fails (`DERA | Documentation Validation`)
* **Error:** `Broken link to nonexistent file` or `Local anchor not found`.
* **Cause:** A markdown link references a missing file or an anchor that does not exist in the target document.
* **Local Reproduction:**
  ```bash
  python scripts/ci/validate_docs.py
  ```
* **Remediation:** Correct the relative path or ensure target heading anchors exist.

---

### Failure 4: Multilingual Parity Fails (`DERA | Multilingual Validation`)
* **Error:** `Missing navigation link to README.<lang>.md` or `Missing required language documentation file`.
* **Local Reproduction:**
  ```bash
  python scripts/ci/validate_i18n.py
  ```
* **Remediation:** Ensure all 10 language documents maintain bidirectional navigation in their top menu according to [`docs/i18n/TRANSLATION_POLICY.md`](../i18n/TRANSLATION_POLICY.md).

---

### Failure 5: Schema Regression Fails (`DERA | Schema Regression`)
* **Error:** `AssertionError: Lists differ: ['public.orders', 'public.users'] != ['public.users', 'public.orders']`
* **Cause:** A modification to DAG dependency sorting or canonical models altered the deterministic output.
* **Local Reproduction:**
  ```bash
  $env:PYTHONPATH="packages/core/src;apps/api/src"
  python -m unittest discover tests/regression/
  ```
* **Remediation:** Inspect `packages/core/src/dera/graph.py` to ensure topological ordering strictly places referenced prerequisites before dependent tables.

---

### Failure 6: TypeScript Type Check Fails (`TypeScript Quality & Typecheck`)
* **Error:** `error TS2307: Cannot find module '@dera/contracts'...`
* **Local Reproduction:**
  ```bash
  npx tsc --noEmit
  ```
* **Remediation:** Verify that all monorepo dependencies and relative imports in `tsconfig.json` resolve correctly.
