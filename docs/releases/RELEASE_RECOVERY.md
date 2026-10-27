# DERA Release Recovery Procedures

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Reference:** [docs/releases/README.md](README.md)  

---

## 1. Principles of Release Recovery

Release engineering failures require decisive, disciplined, and auditable recovery actions. DERA enforces the following core tenets:

1. **Registry Immutability:** Package registries (PyPI, npm) strictly prohibit overwriting published versions. Once a version string is published, it is permanent.
2. **Audit Preservation:** Never delete build logs, qualification reports, or Git audit trails in an attempt to hide a failure.
3. **Transparent Advisory:** If users may have downloaded a flawed package, communicate clearly through GitHub Security Advisories and release notices.
4. **Prefer Forward-Fix:** As detailed in [ROLLBACK_STRATEGY.md](ROLLBACK_STRATEGY.md), forward-fixing via an expedited patch release is safer and more reliable than complex rollbacks.

---

## 2. Standard Operating Procedures by Failure Scenario

### Scenario A: Failed Qualification Gate
- **Trigger:** Test failure, security alert, or checksum mismatch during `.github/workflows/release-qualification.yml`.
- **Status:** Safe. No release was published.
- **Action:**
  1. Halt release preparation.
  2. Inspect failed job logs and diagnostic reports (`reports/test-results.xml`).
  3. Commit fix to the release branch or `main`.
  4. Re-run complete qualification from Stage 1.

### Scenario B: Failed Artifact Build During Publication
- **Trigger:** `python -m build` or `npm pack` fails midway during `.github/workflows/release.yml`.
- **Status:** Potential partial state. Tag may exist in Git, but release is incomplete.
- **Action:**
  1. Inspect whether the Git tag was pushed to remote.
  2. If the tag was pushed but no artifacts were published to public registries, mark the release draft as deleted on GitHub.
  3. Fix the build failure in source code.
  4. Increment pre-release or patch identifier (e.g., from `v0.1.0-rc.1` to `v0.1.0-rc.2`).
  5. **Rule:** Never reuse a tag if external systems might have observed it.

### Scenario C: Corrupted or Tampered Artifacts Detected
- **Trigger:** Checksum verification (`verify_artifacts.py`) reveals a SHA-256 hash mismatch between built files and `SHA256SUMS.txt` or published assets.
- **Status:** Critical security anomaly.
- **Action:**
  1. Immediately quarantine the affected runner or distribution directory.
  2. Audit commit history and workflow run logs for unauthorized access or runner tampering.
  3. If published to GitHub Releases:
     - Mark release as **Withdrawn / Corrupted**.
     - Remove asset attachments from the GitHub release.
     - Document the SHA-256 hash of the compromised asset in an audit log.
  4. Initiate [RELEASE_INCIDENT_RESPONSE.md](RELEASE_INCIDENT_RESPONSE.md).

### Scenario D: Erroneous Release Notes or Metadata
- **Trigger:** Typographical errors, incorrect changelog references, or wrong compatibility details in GitHub Release description.
- **Status:** Low severity. Code and packages are sound.
- **Action:**
  1. Do not retag or republish packages.
  2. Edit the GitHub Release notes directly via the GitHub UI or `gh release edit`.
  3. Commit corrections to `CHANGELOG.md` in `main` for subsequent releases.

### Scenario E: Broken Installation Discovered Post-Publication
- **Trigger:** Downstream users report `ImportError`, missing dependencies, or packaging syntax errors upon installing the published release.
- **Status:** High severity. Users cannot run the software.
- **Action:**
  1. Confirm defect in an isolated clean environment (`pip install dera-core==X.Y.Z`).
  2. On PyPI / npm:
     - **Yank** the broken release (marks package as deprecated and prevents automatic installation, while preserving history for pinned builds).
     - **Never delete** the version file, as deletion breaks reproducible builds for existing users.
  3. Prepare and qualify an immediate forward-fix patch release (`vX.Y.Z+1`).
  4. Update `CHANGELOG.md` noting the defect in `vX.Y.Z` and fix in `vX.Y.Z+1`.

### Scenario F: Critical Security Vulnerability Discovered Post-Publication
- **Trigger:** Zero-day CVE discovered in a dependency or core DERA introspector.
- **Status:** Critical security vulnerability.
- **Action:**
  1. Create private GitHub Security Advisory (GHSA).
  2. Develop and review patch on a private security fork.
  3. Qualify fix against full test suite and security gates.
  4. Publish patch release simultaneously with the public Security Advisory.
  5. Provide explicit upgrade guidance in the advisory.

---

## 3. Automated Release Recovery Verification Workflow

DERA provides an automated recovery verification workflow:
`.github/workflows/release-recovery.yml`

This workflow checks existing published releases:
```bash
# Workflow verifies that:
# 1. The target tag exists in the Git repository and maps to an immutable commit SHA.
# 2. Release assets can be downloaded cleanly.
# 3. Checksums of all downloaded assets match the recorded SHA256SUMS.txt manifest.
```
