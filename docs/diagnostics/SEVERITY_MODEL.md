# DERA Diagnostics — Severity Model

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Module:** `packages/core/src/dera/diagnostics/enums.py`  
**Status:** Canonical Reference  

---

## 1. Severity Classifications

| Tier | Rank | Criteria | Example Condition |
| :--- | :--- | :--- | :--- |
| `CRITICAL` | 5 | Structural integrity violation, model identity collision, or severe corruption that invalidates relational DAG semantics. | `DERA-SCHEMA-002`: Two entities sharing identical canonical ObjectId. |
| `HIGH` | 4 | Severe relational or integrity defect: dangling foreign keys, empty column definitions, mismatched composite foreign key cardinality. | `DERA-SCHEMA-001`: Unresolved relationship target in complete schema. |
| `MEDIUM` | 3 | Performance hazard or missing secondary structural optimization. | Unindexed foreign key column (Phase 8.2). |
| `LOW` | 2 | Maintainability concern, naming anomaly, or non-critical schema drift. | Missing table comment / metadata documentation. |
| `INFORMATIONAL` | 1 | Transparent diagnostic coverage note or uninspected feature notification; not a schema defect. | `DERA-SCHEMA-005`: Unsupported inspection capability for source engine. |

---

## 2. Explainable Severity

Every `DiagnosticFinding` requires a mandatory `severity_rationale` explaining:
1. Why this severity tier was selected.
2. The operational, structural, or performance impact of the observed condition.
3. Why missing metadata was not falsely elevated to critical defect status.
