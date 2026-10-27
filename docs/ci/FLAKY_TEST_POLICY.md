# DERA Flaky Test Management & Quarantine Policy

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Classification:** Official DevSecOps Test Reliability Standard  

---

## 1. Purpose & Core Principles

A continuous integration gate is only as valuable as its determinism. Flaky tests—tests that exhibit both passing and failing results without code changes—erode contributor confidence, waste runner resources, and obscure genuine software defects.

### Core Principles
1. **Zero Silent Exclusions:** Tests must never be deleted, commented out, or silently disabled to make CI pass.
2. **No Blind Retries for Unit Tests:** Deterministic unit tests must pass on the first attempt. Workflows must not use automatic test retry loops to mask flaky logic.
3. **Formal Quarantine Tracking:** Any test exhibiting non-deterministic behavior must be quarantined following the explicit protocol detailed herein, accompanied by an open GitHub tracking issue.
4. **14-Day Remediation SLA:** Quarantined tests must be triaged, debugged, and either fixed or refactored within 14 calendar days.

---

## 2. Common Causes of Flakiness in Database Tooling

| Flakiness Category | Typical Manifestation | DERA Mitigation Strategy |
|---|---|---|
| **Timing & Race Conditions** | Async process or container socket not yet listening | Use deterministic polling readiness (`nc -z` with retries), avoid arbitrary `sleep` calls. |
| **State Pollution** | Subsequent tests failing due to uncleaned temporary files | Use `tempfile.TemporaryDirectory()`, isolate SQLite database instances per test method. |
| **Environment Discrepancies** | Passing on Windows locally, failing on Ubuntu CI | Test path case sensitivity, normalize path separators with `pathlib.Path`. |
| **Order Dependency** | Test passes when run in isolation, fails when run in suite | Ensure test methods have zero dependencies on execution ordering. |
| **External Network Delays** | HTTP timeouts or third-party rate limits | Keep network link validation isolated to weekly `external-links.yml` workflows. |

---

## 3. Quarantine Protocol

When an intermittent failure is observed across multiple CI runs on the same commit:

### Step 1: Evidence Collection
* Capture the failing run ID, runner operating system, Python/Node runtime, and full exception traceback.
* File a GitHub issue labeled `kind/flaky-test` with the title format:  
  `test(flaky): <TestClassName>.<test_method_name> intermittent failure`

### Step 2: Explicit Quarantine Decoration
Quarantine the specific test method using the standard library `@unittest.skip` decorator containing the tracking issue reference:

```python
import unittest

class TestConnectorIntegration(unittest.TestCase):

    @unittest.skip("QUARANTINE: Issue #45 - Socket timeout on slow runner initialization")
    def test_ephemeral_reconnection(self) -> None:
        ...
```

### Step 3: Triage & Root-Cause Remediation
* Isolate the test environment and reproduce using a local loop:
  ```bash
  python -c "
  import subprocess, sys
  for i in range(50):
      res = subprocess.run([sys.executable, '-m', 'unittest', 'tests.integration.test_sqlite_connector.TestSqliteConnector.test_ephemeral_reconnection'])
      if res.returncode != 0:
          print(f'Failed on iteration {i}')
          sys.exit(1)
  print('50 iterations passed successfully.')
  "
  ```
* Address the root cause (e.g., adding explicit file flush, socket polling, or isolation).

### Step 4: Verification & Re-Enablement
* Run at least **100 consecutive iterations** locally without failure.
* Open a pull request removing the `@unittest.skip` decorator.
* Link the pull request to close the tracking issue upon merge.

---

## 4. Permitted Retry Policies

Automated retries are permitted **only** in specific infrastructure-level scenarios where transient external factors are beyond project control:

| Scope | Retries Allowed? | Max Attempts | Conditions |
|---|:---:|:---:|---|
| **Unit & Architecture Tests** | **NO** | 1 | Must pass deterministically on first execution. |
| **Package Manager Downloads** | **YES** | 2 | Handled natively by pip/npm network retry flags. |
| **PostgreSQL Service Readiness** | **YES** | 5 | Service container healthcheck (`nc -z 127.0.0.1 5432`). |
| **External Link Auditing** | **YES** | 3 | Handled by lychee in `external-links.yml`. |
