# Phase 10.2 Structural Complexity Scoring

Scoring version: `1.0.0`. The score is a reproducible AST structure metric, never measured
execution cost, latency, memory demand, query selectivity or an optimization guarantee.

## Exact formula

Score is the sum of count multiplied by weight for these factors across the validated batch.
The maximum AST depth is the maximum across statements, with the root at depth zero.

| Factor | Count definition | Weight |
| --- | --- | --- |
| joins | Join AST nodes | 3 |
| nested_queries | Subquery AST nodes | 3 |
| ctes | CTE AST nodes | 2 |
| max_ast_depth | Maximum edge depth from any statement root | 1 |
| predicate_nodes | Predicate, AND, OR and NOT nodes | 1 |
| aggregates | AggFunc nodes | 2 |
| windows | Window nodes | 3 |
| set_operations | SetOperation nodes | 3 |
| object_references | Table AST nodes, including syntactic CTE references | 1 |

Each node is counted once per factor. Factors can overlap by design. Factors are sorted by name.
The score has no hidden constant, normalization, cap or database-specific cost term.
LOW: score below 25. MODERATE: 25 through 59. HIGH: 60 or more.
`SELECT 1` scores 1 because its literal has depth 1; it has no other factor contributions.

## Rationale and versioning

Weights are engineering policy for readability and review effort: joins, subqueries, windows
and set composition receive three units; CTEs and aggregates receive two; raw depth, predicates
and syntactic object references receive one. They are not fitted to performance measurements.
Scoring counts syntactic references, not distinct catalog objects. Different dialect ASTs may
produce different scores even when SQL strings appear similar.

The response contains every count, weight, contribution, band and scoring_version. A scoring
policy change requires a version change. Report fingerprints bind the complete scoring contract,
rules/report/analysis versions, input digest, dialect, requested options and schema fingerprint.
No timing, random identifier or current timestamp enters normalized diagnostics.

Malformed or resource-rejected SQL has no score. Omitting complexity via request options returns
null, while still running deterministic diagnostics and recording that option in the fingerprint.
