# DERA Artifact Naming, Retention & Security Policy

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Classification:** Official DevSecOps Artifact Standard  

---

## 1. Overview & Objectives

GitHub Actions generates build outputs, test logs, coverage summaries, and security diagnostics. The DERA Artifact Policy defines deterministic naming conventions, strict retention schedules, and sensitive-data safeguards to prevent storage bloat, avoid credential leakage, and ensure audit traceability.

---

## 2. Canonical Artifact Naming Convention

All artifacts uploaded by DERA workflows must strictly follow the canonical naming pattern:

```text
dera-{category}-{platform}-{runtime}-{run-id}-{attempt}
```

### Component Definitions
* `dera`: Mandatory project prefix.
* `{category}`: Functional artifact classification (see [Category Registry](#3-artifact-category-registry-retention-schedule)).
* `{platform}`: Target runner operating system (`linux`, `windows`, `macos`, `multi`).
* `{runtime}`: Execution runtime identifier (`py312`, `py313`, `node22`, `all`).
* `{run-id}`: GitHub Actions run identifier (`${{ github.run_id }}`).
* `{attempt}`: Run attempt number (`${{ github.run_attempt }}`).

### Canonical Examples
* `dera-test-results-linux-py312-40456988257-1`
* `dera-test-results-linux-py313-40456988257-1`
* `dera-build-linux-py313-40456988257-1`
* `dera-diagnostics-python-3.13-linux-40456988257-1`
* `dera-security-codeql-python-linux-40456988207-1`
* `dera-security-codeql-javascript-typescript-linux-40456988207-1`

---

## 3. Artifact Category Registry & Retention Schedule

| Category | Description | Primary Path | Retention Period | Rationale |
|---|---|---|:---:|---|
| **`diagnostics`** | Error traces, debug logs, failed step context | `reports/`, `*.log` | **5 days** | Short-lived triage evidence; rarely needed after PR resolution. |
| **`test-results`** | JUnit XML (`test-results.xml`) and JSON summaries | `reports/` | **14 days** | Review and regression comparison across PR lifecycle. |
| **`coverage`** | LCOV and coverage XML metrics | `coverage/` | **14 days** | Pull request review and quality audit verification. |
| **`build`** | Python distribution packages (`.whl`, `.tar.gz`) | `dist/` | **14 days** | Pre-release distribution validation on `main` branch. |
| **`docs`** | Documentation check reports and navigation logs | `docs-reports/` | **14 days** | Technical documentation verification evidence. |
| **`security`** | CodeQL SARIF static analysis reports | `codeql-results/` | **30 days** | Security audit traceability and vulnerability tracking. |
| **`audit`** | Phase acceptance reports, formal certificates | `docs/audit/` | **90 days** | Governance, regulatory, and milestone verification evidence. |

---

## 4. Artifact Security & Prohibited Content

### 4.1 Prohibited Artifact Data
Artifacts are publicly downloadable by repository contributors and automated tools. Workflows must never upload:
1. Production passwords, API keys, personal access tokens, or webhook secrets.
2. `.env` files, environment configuration dumps, or process environment tables.
3. Private cryptographic keys (`*.pem`, `*.key`, `id_rsa`).
4. Live customer data, real database dumps, or unredacted SQL queries containing sensitive data.

### 4.2 Automated Safety Scanning
Before uploading artifacts, workflows can invoke the DERA Artifact Manager to scan for prohibited files:
```bash
python scripts/ci/artifact_manager.py scan-safe <directory-path>
```
If any forbidden filename or credential pattern is detected, the command exits with code `1`, blocking upload.

---

## 5. Artifact Integrity & SHA-256 Manifests

To ensure artifacts are not corrupted during packaging or download, every artifact bundle includes an authoritative `manifest.json` recording SHA-256 checksums for each constituent file:

```bash
# Generate manifest prior to upload
python scripts/ci/artifact_manager.py manifest reports/ --output reports/manifest.json
```

### Manifest Structure
```json
{
  "directory": "reports",
  "total_files": 2,
  "checksums": {
    "test-results.xml": "b69f2339368fd0d1fe7835496c369181e9aa08048d324f50971a3bf0fca99602",
    "test-summary.json": "055ae790b7508f591e24b1e0c9e2b421bdc7478fe6e7870fa28fc9e470a0ce4d"
  }
}
```

---

## 6. Workflow Implementation Example

```yaml
- name: "Generate Test Artifact Integrity Manifest"
  if: always()
  run: |
    python scripts/ci/artifact_manager.py manifest reports/ --output reports/manifest.json

- name: "Upload Test Execution Artifacts"
  if: always()
  uses: actions/upload-artifact@v7
  with:
    name: dera-test-results-linux-${{ matrix.python-version }}-${{ github.run_id }}-${{ github.run_attempt }}
    path: reports/
    retention-days: 14
    if-no-files-found: ignore
```
