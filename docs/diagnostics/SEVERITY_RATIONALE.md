# Severity Rationale Specification

## Overview

In DERA Phase 8.5, every diagnostic finding must include a clear, human-readable severity rationale. Opaque severity scores or unexplained badges are prohibited. The rationale explains precisely which rule conditions, thresholds, or evidence records led to the assigned severity.

## Rationale Generation Principles

1. **Evidence-Grounded**: The rationale references verified schema facts (such as column count, duplicate index names, or missing referenced tables).
2. **Explicit Rule Logic**: The rationale states the active threshold or condition that triggered the level (e.g., `Exceeds wide table threshold (65 > 50 columns)`).
3. **Override Transparency**: If an authorized override altered the original severity, the rationale reflects both the original evaluation and the override reason with the authorizing actor.
4. **No Speculation**: The rationale does not claim runtime degradation or performance impact unless backed by verified query statistics.

## Standard Rationale Formats

- **Structural Defects (`CRITICAL`/`HIGH`)**:
  `"Rule {rule_id} evaluated {object_name} as {severity} because primary key definition contains nullable columns."`
- **Missing FK Index (`MEDIUM`)**:
  `"Rule DERA-IDX-003 assigned MEDIUM severity because foreign key '{fk_name}' references '{target_table}' without a supporting index on leading columns."`
- **Duplicate Index (`MEDIUM`)**:
  `"Rule DERA-IDX-001 assigned MEDIUM severity because index '{index_a}' is structurally identical to '{index_b}'."`
- **Naming Deviation (`LOW`)**:
  `"Rule DERA-MAINT-003 assigned LOW severity because table name '{table_name}' deviates from configured snake_case pattern."`
