# DERA Diagnostics — Foundational Rules Catalog

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Catalog Package:** `packages/core/src/dera/diagnostics/rules/foundational/`  
**Status:** Canonical Reference  

---

## 1. Catalog Summary

Phase 8.1 introduces five foundational diagnostic rules validating canonical schema integrity, relationship soundness, and metadata completeness:

| Rule ID | Title | Category | Severity | Targets | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DERA-SCHEMA-001` | Unresolved Canonical Relationship Target | `RELATIONSHIPS` | `HIGH` | `foreign_key` | Detects foreign keys targeting non-existent parent tables or columns in complete schemas. |
| `DERA-SCHEMA-002` | Canonical Object Identity Collision | `STRUCTURAL_INTEGRITY` | `CRITICAL` | `table`, `view`, `column` | Detects duplicate canonical ObjectIds generated for distinct entities. |
| `DERA-SCHEMA-003` | Invalid Canonical Relationship Mapping | `RELATIONSHIPS` | `HIGH` | `foreign_key` | Validates composite column counts and flags empty foreign key mappings. |
| `DERA-SCHEMA-004` | Missing Required Canonical Structural Metadata | `METADATA_COMPLETENESS` | `HIGH` | `table` | Detects tables defined with zero columns or empty definitions. |
| `DERA-SCHEMA-005` | Unsupported Inspection Capability | `METADATA_COMPLETENESS` | `INFORMATIONAL` | `database` | Transparently reports unsupported or untested connector feature areas without generating false defects. |
