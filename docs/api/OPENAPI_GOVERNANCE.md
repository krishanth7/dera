# DERA OpenAPI Specification Governance

The OpenAPI 3.1 specification for DERA is treated as a first-class engineering artifact, verified continuously in CI to guarantee zero contract drift.

---

## 1. Specification Location & Generation

The canonical specification is stored at:

```text
docs/api/openapi.v1.json
```

It is generated directly from the live FastAPI application metadata, route decorators, and Pydantic v2 contract schemas:

```bash
# Regenerate snapshot after intentional additive modifications
python scripts/ci/validate_openapi.py --update
```

---

## 2. CI Verification & Zero-Drift Gate

During every CI pull request run, the `contracts-architecture` job executes:

```bash
# Verify live OpenAPI spec matches snapshot (zero drift)
python scripts/ci/validate_openapi.py --check
```

If any developer modifies a route, parameter, or schema without updating the snapshot, or if an unintentional drift occurs, CI fails with an actionable diagnostic message.

---

## 3. Automated Breaking-Change Detection

The validator script (`scripts/ci/validate_openapi.py`) inspects the candidate schema against the committed baseline and flags any of the following regressions:

* **Removed endpoint paths** (`404` risk for existing integrations).
* **Removed HTTP methods** (`405 Method Not Allowed` risk).
* **Added required parameters** (unannounced breaking contract).
* **Changed parameter optionality** (optional parameters made required).
* **Removed 2xx success response status codes** (unexpected client failure).

```text
[ERROR] 1 breaking change(s) detected in candidate OpenAPI specification:
  - Removed endpoint path: '/api/v1/catalogs'
```

Breaking changes are strictly rejected by CI unless approved through a formal architectural RFC and assigned to a new major version.
