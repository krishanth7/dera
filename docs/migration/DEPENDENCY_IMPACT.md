# Dependency Blast Radius & Reachability

**Phase:** 9.2 — Schema Change Classification & Migration Risk Analysis  

---

## 1. Directed Foreign Key Reachability

The dependency analyzer computes downstream impact using reverse reachability over the canonical foreign key multigraph:
- **Direction:** `Child Table (holding FK)` -> `Parent Table (holding PK/UQ)`
- **Reverse Reachability:** For a changed parent table $T$, downstream dependents are discovered by traversing inbound edges where $T$ is the referenced target.

## 2. Blast Radius Metrics
For each affected table, `BlastRadiusMetrics` reports:
- `direct_dependents_count`: Immediate child tables holding foreign keys to $T$.
- `transitive_dependents_count`: Indirect child tables depending on $T$ across multiple FK hops.
- `affected_namespaces`: Distinct schemas hosting dependent tables.
- `max_dependency_depth`: Topological distance to the furthest dependent entity.
- `is_part_of_cycle`: Whether $T$ participates in a cyclic foreign key loop.
