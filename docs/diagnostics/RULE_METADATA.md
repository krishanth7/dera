# DERA Diagnostics — Rule Metadata

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Module:** `packages/core/src/dera/diagnostics/models.py`  
**Status:** Canonical Reference  

---

## 1. Specification

Every rule must statically declare an immutable `RuleMetadata` record:

| Field | Type | Description |
| :--- | :--- | :--- |
| `rule_id` | `str` | Stable machine-readable identifier (e.g. `DERA-SCHEMA-001`). |
| `title` | `str` | Human-readable title describing the diagnostic condition. |
| `description` | `str` | Comprehensive explanation of what the rule detects and why. |
| `version` | `str` | Semantic version string of the rule evaluation logic (e.g. `1.0.0`). |
| `category` | `RuleCategory` | Taxonomy classification (`STRUCTURAL_INTEGRITY`, `RELATIONSHIPS`, etc.). |
| `default_severity` | `DiagnosticSeverity` | Baseline severity (`INFORMATIONAL`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). |
| `supported_object_kinds` | `tuple[str, ...]` | Applicable canonical entities (e.g. `table`, `column`, `foreign_key`). |
| `required_capabilities` | `tuple[str, ...]` | Mandatory inspection capabilities (e.g. `foreign_keys`, `indexes`). |
| `supported_engines` | `tuple[str, ...]` | Target engine dialects. Empty tuple denotes all supported relational engines. |
| `applicability_summary` | `str` | Concise summary of conditions under which the rule applies. |
| `evidence_requirements` | `str` | Description of evidence keys and types required to support findings. |
| `recommendation_template`| `str` | Deterministic template for remediation advisory guidance. |
| `documentation_url` | `str` | Canonical reference URL for detailed engineering background. |
