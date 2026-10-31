# Structural Coupling Diagnostics (DERA-MNT-006)

## Overview

Structural coupling measures the total relational degree of a table in the database multigraph. A table linked to dozens of distinct tables via incoming and outgoing foreign keys exhibits high architectural coupling.

Rule `DERA-MNT-006` identifies entities where combined foreign key degree exceeds configured maintainability thresholds.

## Thresholds

- **Baseline Coupling** (`max_structural_coupling_degree`, default: 12 total edges): Emits `LOW` severity finding.
- **Elevated Coupling** (`elevated_coupling_degree`, default: 24 total edges): Emits `MEDIUM` severity finding.

## Metric Definition

$$\text{total\_degree}(v) = \text{in\_degree}(v) + \text{out\_degree}(v)$$

Where:
- $\text{in\_degree}(v)$ is the count of foreign keys pointing to table $v$.
- $\text{out\_degree}(v)$ is the count of foreign keys originating from table $v$.

## Non-Negotiable Constraint

High coupling is not inherently a defect: junction tables or central domain roots often have elevated connectivity by design. Findings are classified as maintainability review candidates, not definitive database corruption.
