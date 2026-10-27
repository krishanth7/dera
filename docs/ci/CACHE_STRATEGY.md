# DERA CI Cache Strategy & Security Architecture

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Classification:** Official DevSecOps Caching Standard  

---

## 1. Executive Summary

Caching in DERA's CI pipeline accelerates dependency resolution, package installation, and build artifacts without compromising build determinism, security boundaries, or test reproducibility.

A cache hit must only accelerate execution time; it must never dictate build correctness.

---

## 2. Cache Architecture by Runtime

### 2.1 Python Dependency Caching (`pip`)
* **Tool:** `actions/setup-python` native cache mechanism (`cache: "pip"`).
* **Cached Directories:** `~/.cache/pip` (Linux) / `%LocalAppData%\pip\Cache` (Windows).
* **Mechanism:**
  * Pip package wheels and tarballs downloaded from PyPI are cached on the runner.
  * Virtual environments (`.venv/`) are **intentionally not cached** across runs. Reconstructing virtual environments in each job guarantees that C-extension binary paths and dynamic linker dependencies remain clean and uncorrupted.
* **Workflows Implementing Pip Caching:**
  * Primary CI backend matrix: `ci.yml` (`python-qualification`)
  * Database connector integration: `ci.yml` (`database-integration`)
  * Dependency security scanning: `dependency-security.yml`
  * Static security tests: `security-tests.yml`

### 2.2 Node.js Monorepo Workspace Caching (`npm`)
* **Tool:** `actions/setup-node` native cache mechanism (`cache: "npm"`).
* **Cached Directory:** `~/.npm` global package tarball cache.
* **Mechanism:**
  * Caches compressed package tarballs indexed by `package-lock.json` hash.
  * `node_modules/` is **intentionally not cached** directly. Dependencies are deterministically unpacked via `npm ci`, which verifies package checksums against `package-lock.json` on every installation.
* **Workflows Implementing Npm Caching:**
  * Primary CI frontend: `ci.yml` (`frontend-qualification`)
  * Documentation quality gate: `ci.yml` (`documentation-quality`)
  * Markdown linting: `documentation.yml`
  * Dependency auditing: `dependency-security.yml`

---

## 3. Cache Key Design & Determinism

Cache keys are structured hierarchically to prevent cross-runtime or cross-operating-system collisions:

### Python Cache Key Structure
```text
setup-python-${RUNNER_OS}-${RUNNER_ARCH}-${DISTRO}-python-${PYTHON_VERSION}-pip-${LOCKFILE_HASH}
```
* Example: `setup-python-Linux-x64-24.04-Ubuntu-python-3.13.16-pip-6d417f3aa9c91468...`
* **Fallback Restore Keys:** If an exact lockfile match is unavailable, `setup-python` falls back to prefix matching (`setup-python-Linux-...-python-3.13-pip-`), reusing shared common wheels.

### Node.js Cache Key Structure
```text
node-cache-${RUNNER_OS}-${RUNNER_ARCH}-npm-${PACKAGE_LOCK_HASH}
```
* Example: `node-cache-Linux-x64-npm-77ba991d02a750808fb55b0a1c37371aef379a3ee447...`

---

## 4. Cache Security & Trust Boundaries

### 4.1 Fork Pull Request Cache Isolation
* GitHub Actions enforces native trust boundary isolation: pull requests originating from forks have **read-only access** to the default branch (`main`) cache.
* A fork PR cannot create, overwrite, or poison cache entries utilized by `main` or subsequent pull requests.

### 4.2 Prohibited Cache Content
Under no circumstances may the following items be stored in GitHub Actions caches:
* Authentication tokens, API keys, or private SSH keys.
* `.env` files or test database connection credentials.
* Compiled untrusted binaries or unverified third-party executable scripts.
* Live SQLite database files or ephemeral database volumes.

---

## 5. Cold-Cache Reproducibility Verification

DERA's engineering standards require periodic cold-cache validation to guarantee that dependencies resolve cleanly without relying on existing cache entries.

### Validation Procedure
```bash
# 1. Clean local caches
pip cache purge
npm cache clean --force

# 2. Execute full cold build
python scripts/development/dev.py all
```
* During CI execution, when a new dependency version is introduced or a lockfile is updated, a cache miss triggers a clean download and establishes a new cache key without failing qualification.

---

## 6. Cache Retention & Maintenance

* **Size Limit:** GitHub Actions limits repository cache storage to **10 GB**.
* **Eviction Policy:** GitHub automatically evicts caches not accessed in the last **7 days**. When the 10 GB limit is approached, the oldest caches are purged based on Least Recently Used (LRU) policy.
* **Automated Audit:** [`.github/workflows/cache-maintenance.yml`](../../.github/workflows/cache-maintenance.yml) runs weekly on Sundays at 02:00 UTC using [`scripts/ci/cache_maintenance.py`](../../scripts/ci/cache_maintenance.py) to audit cache utilization and log storage trends.
