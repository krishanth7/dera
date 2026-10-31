# Diagnostic Finding Prioritization Specification

## Overview

DERA Phase 8.5 establishes deterministic, transparent prioritization for diagnostic findings. Rather than arbitrary black-box machine-learning rankings, findings are ordered using an explainable mathematical formula and a deterministic multi-key sort hierarchy.

## Priority Score Formula

The priority score $S$ is computed as:

$$S = (W_{\text{sev}} \times 1000) + (W_{\text{conf}} \times 100) + (W_{\text{cls}} \times 10) + W_{\text{scope}}$$

Where weights are deterministically assigned:
- **Severity Weights ($W_{\text{sev}}$)**:
  - `CRITICAL`: 10
  - `HIGH`: 7
  - `MEDIUM`: 4
  - `LOW`: 2
  - `INFORMATIONAL`: 1
- **Confidence Weights ($W_{\text{conf}}$)**:
  - `VERIFIED`: 5
  - `CONDITIONAL`: 3
  - `INCOMPLETE`: 1
  - `UNSUPPORTED`: 0
- **Classification Weights ($W_{\text{cls}}$)**:
  - `CONFIRMED_STRUCTURAL_DEFECT`: 8
  - `POTENTIAL_ENGINEERING_CONCERN`: 6
  - `OPTIMIZATION_CANDIDATE`: 4
  - `MAINTAINABILITY_CONCERN`: 3
  - `NAMING_CONVENTION_DEVIATION`: 1
  - Other: 0
- **Scope Weight ($W_{\text{scope}}$)**:
  - Schema/Global: 3
  - Table: 2
  - Column/Index/Constraint: 1

## Priority Rank

Based on the calculated priority score, findings are grouped into ranks:
- **`URGENT`**: Score >= 8,000 (Critical/High verified defects)
- **`IMPORTANT`**: Score between 5,000 and 7,999
- **`NORMAL`**: Score between 2,000 and 4,999
- **`LOW_PRIORITY`**: Score < 2,000

## Deterministic Stable Sort Hierarchy

To guarantee byte-for-byte reproducible reports regardless of system architecture or database concurrency, findings are ordered by:
1. `priority_score` (Descending)
2. `severity` (Descending rank)
3. `confidence` (Descending rank)
4. `rule_id` (Ascending lexicographical)
5. `object_id` (Ascending lexicographical)
6. `fingerprint` (Ascending lexicographical)
