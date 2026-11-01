# Finding Classification Specification

## Overview

Finding classification provides an orthogonal taxonomy to severity. Severity measures *urgency and risk*, whereas classification measures the *nature of the defect or observation*. DERA Phase 8.5 strictly separates classification from severity to prevent subjective or stylistic issues from escalating to critical levels.

## Canonical Classifications

The system recognizes eight discrete classifications:

| Classification | Meaning | Typical Rules |
| :--- | :--- | :--- |
| `CONFIRMED_STRUCTURAL_DEFECT` | Verifiable schema flaw violating relational integrity | `DERA-CON-001`, `DERA-CON-002` |
| `POTENTIAL_ENGINEERING_CONCERN` | Architectural hazard that may introduce production issues under load | `DERA-CON-003`, `DERA-REL-002` |
| `OPTIMIZATION_CANDIDATE` | Redundant schema artifact consuming storage or write overhead | `DERA-IDX-001`, `DERA-IDX-002` |
| `MAINTAINABILITY_CONCERN` | Architectural complexity exceeding maintainability thresholds | `DERA-MAINT-001`, `DERA-MAINT-004` |
| `NAMING_CONVENTION_DEVIATION` | Discrepancy against configured engineering nomenclature | `DERA-MAINT-003` |
| `INFORMATIONAL_OBSERVATION` | Informational architectural observation | `DERA-SCHEMA-001` |
| `METADATA_LIMITATION` | Observation caused by partial or restricted database permissions | Metadata capability checks |
| `INTERNAL_INSPECTION_INTEGRITY_ISSUE` | Engine-level anomaly during schema reflection | Internal reflection audits |

## Classification Rules

- A naming deviation must **never** be classified as a `CONFIRMED_STRUCTURAL_DEFECT`.
- An optimization candidate must have verified duplicate or redundant structure.
- Classification is immutable once evaluated unless an authorized rule configuration change occurs.
