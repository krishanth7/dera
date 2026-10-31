# Relationship Concentration & Centrality Diagnostics

## Overview

Relationship concentration diagnostics evaluate how foreign key edges are distributed across relational entities. In complex enterprise databases, certain central entities ("hub tables", e.g., `tenants`, `users`, `organizations`) become extreme reference sinks or sources.

Excessive relationship concentration introduces significant migration risks:
- Deleting or migrating a central table causes cascading locking issues.
- Massive dependency fan-in complicates transactional isolation.
- Schema changes to hub tables require high coordination across engineering teams.

## Graph Centrality Metrics

Reusing Phase 6.3/6.4 graph structures:
- `in_degree`: Total incoming foreign key references (dependents referencing this table as parent).
- `out_degree`: Total outgoing foreign key references (prerequisite parents this table depends upon).
- `total_degree`: Sum of in-degree and out-degree.
- `transitive_dependents_count`: Bounded reverse reachability blast radius.

## Integration with Phase 8.3 & 8.4

Phase 8.3 rules (`DERA-DEP-003`, `DERA-DEP-004`) evaluate directional fan-in and blast radius. Phase 8.4 rule `DERA-MNT-006` evaluates total structural coupling for maintainability reviews.
