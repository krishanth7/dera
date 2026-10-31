# DERA Phase 8.3 — Relationship & Dependency Diagnostics Overview

## 1. Engineering Mission
DERA Phase 8.3 introduces deterministic relationship and dependency intelligence into the DERA Phase 8 diagnostic engine. Building on Phase 6.3 foreign key graph construction, Phase 6.4 topological and strongly connected component (SCC) dependency analysis, and the Phase 8.1 deterministic diagnostic engine, Phase 8.3 executes read-only, explainable, and provable analysis over database relationships and dependency structures.

## 2. Core Architectural Guarantees
- **Strictly Read-Only**: Analyzes canonical schemas, `ForeignKeyGraph` multigraph structures, and `DependencyAnalysisResult` models without issuing database queries or modifying source database states.
- **Zero AI/LLM/ML**: All evaluations rely on deterministic graph algorithms (Tarjan/Kosaraju SCC decomposition, Kahn topological ordering, bounded BFS reverse reachability, and multigraph parallel edge grouping).
- **Edge Direction Convention**: Referencing child table $\to$ Referenced parent table (`order_items` $\to$ `orders` $\to$ `customers`). Preserved uniformly across all diagnostic rules.
- **Explainable Evidence**: Every finding includes affected and related object IDs, observed vs. expected values, structured context, and deterministic SHA-256 fingerprints.
- **Zero Fabrication**: Incomplete catalog permissions and missing namespaces are explicitly distinguished from broken foreign keys.

## 3. Rule Catalog Overview

| Rule ID | Title | Category | Severity | Target Object | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DERA-REL-001` | Relationship Graph Structural Integrity | RELATIONSHIPS | HIGH | `ForeignKeyEdge` | Detects edges referencing non-existent nodes or lacking column mappings |
| `DERA-REL-002` | Unresolved Foreign Key Relationship Target | RELATIONSHIPS | HIGH / LOW | `UnresolvedReference` | Audits foreign key targets unresolvable due to missing entities or scope restrictions |
| `DERA-REL-003` | Composite Foreign Key Mapping Integrity | RELATIONSHIPS | HIGH | `ForeignKeyEdge` | Validates column count parity and ordinal mapping in composite foreign keys |
| `DERA-REL-004` | Cross-Namespace Dependency Structure | RELATIONSHIPS | INFORMATIONAL | `ForeignKeyEdge` | Discovers relationships spanning distinct database schemas/namespaces |
| `DERA-DEP-001` | Circular Foreign Key Dependencies & SCCs | DEPENDENCIES | MEDIUM / LOW | `StronglyConnectedComponent` | Identifies self-referencing loops and multi-table circular dependency cycles |
| `DERA-DEP-002` | Deep Dependency Chains | DEPENDENCIES | LOW / INFORMATIONAL | `TableNode` | Flags tables exceeding configured upstream dependency depth thresholds |
| `DERA-DEP-003` | High Dependency Concentration | DEPENDENCIES | LOW / INFORMATIONAL | `TableNode` | Identifies high fan-in architectural hubs and high fan-out consumers |
| `DERA-DEP-004` | Structural Change Impact Radius | DEPENDENCIES | LOW / INFORMATIONAL | `TableNode` | Discovers downstream blast radius candidates reachable via reverse dependencies |
