# Release Documentation Procedures

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Lead Maintainer:** [Krishanth](https://github.com/krishanth7)  
**License:** [MIT License](../../LICENSE)  

---

## 1. Overview & Objectives

Every release of DERA represents an immutable snapshot of software behavior. Clear, accurate, and disciplined release documentation is essential to ensure users can safely upgrade, understand new capabilities, and adapt to breaking changes or security updates.

This document formalizes the release documentation procedures for both **pre-releases** (alpha, beta, release candidate) and **stable releases** (major, minor, patch).

---

## 2. Release Types & Documentation Requirements

| Release Level | Version Pattern | Scope & Intent | Mandatory Documentation Deliverables |
|---|---|---|---|
| **Alpha / Prototype** | `v0.1.0-alpha.X` | Early engineering previews; rapid iteration on core algorithms. | • Brief release notes highlighting tested capabilities.<br>• Known limitations and non-implemented areas clearly flagged.<br>• Non-production disclaimer. |
| **Beta / Preview** | `v0.1.0-beta.X` | Broader developer testing; connector and schema stability checks. | • Release notes with detailed test scenarios.<br>• Database compatibility matrix snapshot.<br>• Breaking change notices if schemas or contracts changed. |
| **Release Candidate (RC)** | `v0.X.0-rc.X` | Feature freeze; testing release gates and end-to-end qualification. | • Complete draft changelog.<br>• Fresh installation and quickstart test verification.<br>• Translation synchronization readiness assessment. |
| **Patch Release** | `v0.X.Y` | Bug fixes, security patches, documentation corrections. | • Focused changelog entry in `CHANGELOG.md`.<br>• Regression test evidence.<br>• Security advisory reference if addressing a vulnerability. |
| **Minor Release** | `v0.Y.0` | New backwards-compatible features, new database connectors. | • Full changelog entry with contributor acknowledgments.<br>• Updated compatibility matrix in root README and translations.<br>• Updated API specifications. |
| **Major Release** | `vX.0.0` | Significant architectural evolutions, breaking contract changes. | • Dedicated migration and upgrade guide.<br>• Explicit breaking-change deprecation notices.<br>• Full 10-language README synchronization. |

---

## 3. Core Release Documentation Deliverables

### 3.1 Changelog Maintenance (`CHANGELOG.md`)
DERA adheres to the [Keep a Changelog](https://keepachangelog.com/) format and [Semantic Versioning](https://semver.org/):
- **Sections:**
  - `Added` for new features or database dialects.
  - `Changed` for modifications in existing behavior.
  - `Deprecated` for soon-to-be-removed features.
  - `Removed` for features removed in this release.
  - `Fixed` for any bug fixes.
  - `Security` in case of vulnerability fixes.
- Every entry should reference the pull request number and contributor handle where appropriate.

### 3.2 GitHub Release Notes
GitHub Releases must contain:
1. **Summary:** 2–3 sentences summarizing the purpose and key additions of the release.
2. **Highlights:** Bulleted list of primary capabilities or architectural milestones.
3. **Database Compatibility:** Explicit list of verified database versions (e.g., PostgreSQL 14–16, SQLite 3.35+).
4. **Breaking Changes & Migration:** Step-by-step guidance on updating configuration, API calls, or schemas.
5. **Security Considerations:** Explicit confirmation of non-AI deterministic design and read-only database invariants.
6. **Contributors:** Sincere acknowledgment of all community contributors who submitted code, docs, or bug reports.

### 3.3 Documentation Version References
Before tagging a release:
- Update version strings in `pyproject.toml`, `package.json`, and contracts specifications.
- Verify that CLI help text (`dev.py --version` or CLI commands) reports the matching version.
- Ensure documentation links pointing to specific release tags resolve to valid Git references.

### 3.4 Installation & Setup Verification
- Test installation instructions on clean environments (Windows PowerShell, Linux bash, macOS zsh):
  ```bash
  git clone https://github.com/krishanth7/dera.git
  cd dera
  python -m venv .venv
  # Activate venv and verify dev.py all
  python scripts/development/dev.py all
  ```
- Verify that no prerequisite packages or environment variables are omitted from `docs/development/SETUP.md`.

### 3.5 Security Advisories & Vulnerability Disclosures
- If a release resolves a security vulnerability:
  - Do not disclose exploit details prior to the release publication.
  - Follow coordinated disclosure policies documented in [`SECURITY.md`](../../SECURITY.md).
  - Draft a GitHub Security Advisory (GHSA) and assign a CVE if applicable.
  - Reference the security advisory identifier in the changelog and release notes.

### 3.6 Translation Impact Assessment
- Assess whether the release alters:
  - The **Feature Status Matrix** in the root README.
  - The **Database Compatibility Matrix**.
  - **Quickstart commands** or core installation steps.
- If changes occurred, follow [Translation Maintenance](../i18n/TRANSLATION_MAINTENANCE.md) to open follow-up issues for updating the nine international READMEs (`es`, `fr`, `de`, `pt`, `it`, `ja`, `ko`, `zh-CN`, `ru`).

---

## 4. Pre-Release Verification Protocol

Before any release tag is published on GitHub, the maintainer must complete the following validation checklist:

```bash
# 1. Verify code formatting and linting
python scripts/development/dev.py lint

# 2. Verify all test suites pass
python scripts/development/dev.py test

# 3. Verify TypeScript type checking
python scripts/development/dev.py typecheck

# 4. Verify documentation links, markdownlint, and mermaid diagrams
npm run docs:check

# 5. Verify 10-language navigation and parity
python scripts/ci/validate_i18n.py

# 6. Verify full baseline execution
python scripts/development/dev.py all
```

- [ ] All automated GitHub Actions status checks are green on `main`.
- [ ] `CHANGELOG.md` is updated with all merged pull requests since the prior release.
- [ ] Breaking changes (if any) are highlighted with step-by-step migration notes.
- [ ] Installation instructions tested against a clean environment.
- [ ] Maintainer signs and pushes the Git annotated tag (e.g., `git tag -s v0.1.0-alpha.1 -m "Release v0.1.0-alpha.1"`).
