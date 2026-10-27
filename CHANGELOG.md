# Changelog

All notable changes to the **DERA** (Database Engineering & Reverse Analysis) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Release qualification framework and dry-run execution workflow (`.github/workflows/release-qualification.yml`).
- Semantic Versioning 2.0.0 and workspace consistency validation engine (`scripts/release/validate_version.py`).
- Machine-readable release manifest schema validation and generation (`scripts/release/validate_manifest.py`).
- Cryptographic SHA-256 artifact integrity and naming verification engine (`scripts/release/verify_artifacts.py`).
- Release candidate qualification checklist and multi-tier qualification matrix (`docs/releases/RELEASE_CANDIDATE_CHECKLIST.md`, `docs/releases/RELEASE_QUALIFICATION.md`).
- Release lifecycle design, human approval boundaries, and release security gates (`docs/releases/RELEASE_LIFECYCLE.md`).
- Release recovery, rollback, forward-fix, and incident response procedures (`docs/releases/RELEASE_RECOVERY.md`, `docs/releases/ROLLBACK_STRATEGY.md`, `docs/releases/RELEASE_INCIDENT_RESPONSE.md`).
- Automated release regression test suite (`tests/release/test_release_qualification.py`).

---

## [0.1.0-alpha.3] - 2026-10-27

### Added

- Continuous Integration performance management, pip caching, and structured test reporting (`scripts/ci/test_reporter.py`).
- CI artifact naming standards, category registry, and SHA-256 manifest generation (`scripts/ci/artifact_manager.py`).
- Full 10-language internationalized documentation validation and navigation workflows (`scripts/ci/validate_i18n.py`).
- CodeQL static application security testing for Python, JavaScript/TypeScript, and GitHub Actions (`.github/workflows/codeql.yml`).
- Automated dependency review and Dependabot supply-chain security configuration.
- Conventional PR title and contributor checklist readiness qualification gates (`scripts/ci/validate_pr_title.py`, `scripts/ci/validate_pr_readiness.py`).
- Main CI matrix test qualification for Python 3.12 and 3.13 (`.github/workflows/ci.yml`).

### Security

- Enforced read-only permission defaults (`permissions: contents: read`) across all standard CI workflows.
- Added strict pinned actions and disallowed untrusted external script execution.

---

## [0.1.0-alpha.2.0] - 2026-10-26

### Added

- Comprehensive documentation governance, ownership matrix, and maintenance schedules (`docs/governance/`).
- Multilingual README translations across 10 international languages (`docs/i18n/`).
- Formal security policy, threat model, vulnerability triage SLA, and reporting procedures (`SECURITY.md`, `docs/security/`).
- Code of Conduct and contributor onboarding guides (`CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`).

### Fixed

- Preserved historical non-standard version reference `v0.1.0-alpha.2.0` in documentation and tag records without rewriting Git history.

---

## [0.1.0-alpha.1] - 2026-10-26

### Added

- Initial monorepo foundation with Python core (`packages/core`), database connectors (`packages/connectors`), FastAPI application (`apps/api`), and Next.js frontend scaffold (`apps/web`).
- Shared TypeScript schema contracts and JSON Schema definitions (`packages/contracts`).
- Cross-platform development CLI utility (`scripts/development/dev.py`).
- Pure Python deterministic relational graph resolution using Kahn DAG algorithm.
- Read-only SQLite and PostgreSQL 16 schema introspection engine.

---

[Unreleased]: https://github.com/krishanth7/dera/compare/v0.1.0-alpha.3...HEAD
[0.1.0-alpha.3]: https://github.com/krishanth7/dera/compare/v0.1.0-alpha.2.0...v0.1.0-alpha.3
[0.1.0-alpha.2.0]: https://github.com/krishanth7/dera/compare/v0.1.0-alpha.1...v0.1.0-alpha.2.0
[0.1.0-alpha.1]: https://github.com/krishanth7/dera/releases/tag/v0.1.0-alpha.1
