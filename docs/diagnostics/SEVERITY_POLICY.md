# Severity Policy Specification

## Overview

DERA Phase 8.5 formalizes a deterministic, conservative severity policy across all diagnostic categories. The severity assignment system ensures that findings are graded objectively based on structural defect evidence rather than subjective impressions or unverified runtime impact.

## Supported Severity Levels

The unified severity hierarchy comprises five discrete levels:

| Severity | Definition | Permitted Triggers |
| :--- | :--- | :--- |
| `CRITICAL` | Severe schema integrity defect or broken constraint preventing relational guarantees | Corrupted PK, unresolvable primary key target |
| `HIGH` | High risk of data inconsistency, broken reference, or severe maintainability hazard | Broken foreign keys, unresolvable FK references, severe cross-namespace entanglement |
| `MEDIUM` | Structural optimization opportunity or potential maintenance bottleneck | Redundant/duplicate indexes, missing FK indexes, high coupling |
| `LOW` | Stylistic discrepancy, mild maintainability concern, or naming deviation | Naming standard deviation, wide tables, mild cyclomatic complexity |
| `INFORMATIONAL` | Informative observation, engine feature notation, or documentation item | Schema documentation omissions, informational stats |

## Conservative Severity Derivation

In accordance with strict database reliability engineering standards, the severity policy prohibits escalating findings to `CRITICAL` without verified structural defect evidence:

- **Wide tables**: Assigned `LOW` or `MEDIUM` based on column count thresholds, never `CRITICAL`.
- **Missing foreign key indexes**: Assigned `MEDIUM` (conditional on workload query patterns), never `CRITICAL`.
- **Cyclic dependencies**: Assigned `MEDIUM` or `HIGH` depending on cycle span and SCC size, never `CRITICAL`.
- **Naming convention deviations**: Assigned `LOW` or `INFORMATIONAL`, never `CRITICAL`.
- **Large namespaces**: Assigned `LOW`, never `CRITICAL`.

## Severity Policy Versioning

The severity policy is strictly versioned (`SEVERITY_POLICY_VERSION = "1.0.0"`). Each diagnostic report records the active policy version to guarantee auditability and repeatability across engine upgrades.

## Severity Overrides

Authorized users may apply scoped overrides to adjust effective severity. Every override must record:
- Finding fingerprint or rule scope
- Original severity and effective severity
- Authorized actor identifier
- Reason for override
- Timestamp and policy version
