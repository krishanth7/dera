# DERA Phase 8.3 — Relationship & Dependency Severity Model

## 1. Severity Levels & Criteria
DERA Phase 8.3 maps relationship and dependency findings to the established 4-tier severity model:

| Severity | Definition | Applicable Phase 8.3 Findings |
| :--- | :--- | :--- |
| `HIGH` | Verified metadata defects, broken internal graph edges, or invalid composite foreign key mappings that prevent execution. | `DERA-REL-001` (missing endpoints, empty mappings), `DERA-REL-002` (missing tables/columns within scope), `DERA-REL-003` (composite length mismatch, missing column references). |
| `MEDIUM` | Structural hazards affecting transactional execution or migration sequencing. | `DERA-DEP-001` (multi-table circular dependencies), `DERA-DEP-002` (depth $\ge 2\times$ threshold), `DERA-DEP-003` (degree $\ge 2\times$ threshold). |
| `LOW` | Architectural complexity or standard hierarchical patterns. | `DERA-DEP-001` (single-node self-loops), `DERA-REL-002` (permission/scope restricted unresolved targets), `DERA-DEP-002` (depth $\ge 1\times$ threshold), `DERA-DEP-003` (degree $\ge 1\times$ threshold), `DERA-DEP-004` (impact radius $\ge 1\times$ threshold). |
| `INFORMATIONAL` | Structural patterns provided for architecture and modularity visibility. | `DERA-REL-004` (cross-namespace relationships), `DERA-DEP-004` (moderate impact radius). |

## 2. Dynamic Severity Escalation
For quantitative rules (`DERA-DEP-002`, `DERA-DEP-003`, `DERA-DEP-004`), findings start at `LOW` or `INFORMATIONAL` at the configured baseline threshold, and dynamically escalate to `MEDIUM` when observed counts reach twice ($2\times$) the threshold.
