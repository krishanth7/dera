# Complex Dependency Topology Diagnostics (DERA-MNT-007)

## Overview

Circular foreign key references severely impact database maintainability:
- Pure topological sorting is impossible.
- Table truncation and data seeding require disabling constraints or deferring checks.
- Zero-downtime schema migrations require intricate multi-phase nullable FK deployments.

While small 2-table mutual references (or self-referencing hierarchy trees) are handled by `DERA-DEP-001`, `DERA-MNT-007` specifically audits **complex cyclic components**: Strongly Connected Components (SCCs) containing 3 or more tables or multi-cycle entangled topologies.

## Evaluation Semantics

1. Reuses Phase 6.4 Tarjan's SCC and Johnson's elementary cycle analysis from `DependencyAnalyzer`.
2. Identifies cyclic SCCs with:
   - $\ge 3$ member tables, or
   - $> 1$ distinct elementary cycles.
3. **Severity**:
   - `LOW`: 3 to 4 member tables.
   - `MEDIUM`: $\ge 5$ member tables or $\ge 3$ intersecting cycles.

## Recommendations

- Introduce intermediate join/link tables to break the direct cyclical dependency.
- Make at least one foreign key nullable to establish a valid insertion order.
- Decouple distinct lifecycle domains into asynchronous events or soft references.
