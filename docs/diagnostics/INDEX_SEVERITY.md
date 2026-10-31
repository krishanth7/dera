# Diagnostic Severity Rationale for Indexes and Constraints

## 1. Classification Model
DERA maps all index and constraint findings to explicit `DiagnosticSeverity` tiers based on structural evidence:

| Severity | Description | Phase 8.2 Examples |
| :--- | :--- | :--- |
| **CRITICAL** | Total system failure, data loss risk | N/A in static analysis |
| **HIGH** | Structural defect, broken reference, corruption | Missing PK columns (`DERA-CON-001`), Missing FK source/target columns (`DERA-CON-002`), Index referencing missing column (`DERA-IDX-004`), Empty CHECK clause (`DERA-CON-004`) |
| **MEDIUM** | Storage/write waste, performance risk | Exact duplicate index (`DERA-IDX-001`), Unindexed foreign key (`DERA-IDX-003`), Duplicate unique constraint (`DERA-CON-003`) |
| **LOW** | Minor redundancy, review opportunity | Leftmost prefix candidate (`DERA-IDX-002`), Unique constraint duplicating PK (`DERA-CON-003`), Unresolved external FK target (`DERA-CON-002`) |
| **INFORMATIONAL** | Metadata observation | Inert structural metadata |

## 2. Severity Rationale Field
Every finding requires an explicit `severity_rationale` explaining why that severity was assigned, ensuring audit transparency.
