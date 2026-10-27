# DERA Release Engineering & Qualification Hub

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **License:** [MIT License](../../LICENSE)  

---

## 1. Overview & Core Philosophy

DERA's release engineering framework guarantees that every published artifact, container, and library is **deterministic, verifiable, auditable, and secure**. As a mission-critical database engineering platform, DERA adheres to strict supply-chain security standards and explicit human authorization gates.

Release publication is never automatic. Every prospective release passes through rigorous qualification, artifact checksum verification, and formal maintainer sign-off.

---

## 2. Release Engineering Architecture & Documentation Map

| Document | Purpose & Key Topics | Primary Audience |
|---|---|---|
| [**RELEASE_LIFECYCLE.md**](RELEASE_LIFECYCLE.md) | 10-stage release lifecycle, Semantic Versioning 2.0.0 policy, and canonical version source of truth | Maintainers & Contributors |
| [**RELEASE_CANDIDATE_CHECKLIST.md**](RELEASE_CANDIDATE_CHECKLIST.md) | Pre-flight qualification checklist for verifying source revisions and test gates | Release Engineers |
| [**RELEASE_QUALIFICATION.md**](RELEASE_QUALIFICATION.md) | Release qualification matrix, CI/Security gates, human approval boundaries, provenance, and reproducibility | DevSecOps & Maintainers |
| [**RELEASE_RECOVERY.md**](RELEASE_RECOVERY.md) | Standard operating procedures for handling failed builds, corrupt artifacts, and compromised packages | Release Engineers & SRE |
| [**ROLLBACK_STRATEGY.md**](ROLLBACK_STRATEGY.md) | Rollback versus forward-fix decision matrices across packages, applications, and database migrations | Architecture & SRE |
| [**RELEASE_INCIDENT_RESPONSE.md**](RELEASE_INCIDENT_RESPONSE.md) | Security and operational incident response protocol for published release anomalies | Security Lead & Maintainer |

---

## 3. Release Safety Principles

1. **Explicit Human Authorization:** No release candidate is ever published to public registries (PyPI, npm, GitHub Releases) without deliberate maintainer approval.
2. **Immutable Release Identity:** Published versions map deterministically to an exact 40-character Git commit SHA and tag.
3. **Cryptographic Integrity:** Every built artifact is accompanied by a SHA-256 digest recorded in both `SHA256SUMS.txt` and a machine-readable `manifest.json`.
4. **Least-Privilege Qualification:** Qualification and dry-run workflows run with read-only permissions (`permissions: contents: read`) and zero access to publishing credentials.
5. **No Premature Stable Claims:** In development phases, versioning strictly denotes pre-release channels (`-alpha`, `-beta`, `-rc`). Stable `1.0.0` is released only upon complete enterprise qualification.

---

## 4. Release Tooling Reference

The repository provides in-tree deterministic release management utilities:

```bash
# Validate workspace version synchronization across Python and TypeScript
python scripts/release/validate_version.py --check-consistency

# Validate a release candidate tag against SemVer 2.0.0
python scripts/release/validate_version.py --tag "v0.1.0-rc.1" --require-candidate

# Verify artifact naming conventions and SHA-256 digests in dist/
python scripts/release/verify_artifacts.py --dist-dir dist

# Validate or generate machine-readable release manifest
python scripts/release/validate_manifest.py --manifest dist/manifest.json --dist-dir dist
```
