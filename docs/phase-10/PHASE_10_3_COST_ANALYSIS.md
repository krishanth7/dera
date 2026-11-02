# Phase 10.3 Cost and Cardinality Analysis

PostgreSQL costs are planner units, not milliseconds. MySQL query_cost is a distinct planner
unit. MariaDB and SQLite costs remain unavailable in this implementation. Cross-engine cost
comparison is unsupported. Costs from parent and child nodes are never added together.

The summary reports a single root's inclusive startup/total estimate when available and the five
nodes with highest reported inclusive cost (descending, then stable node ID). This is an estimate
ranking, not identification of slow runtime operations. Exclusive costs, child-cost subtraction,
worker summation, memory budgets and measured bottleneck attribution are intentionally absent.

PostgreSQL node actual rows and times are reported averages per invocation; loops remain a
separate value. MariaDB r_rows is average rows read per invocation and r_total_time_ms is
cumulative inclusive time. MySQL JSON v1 and SQLite EQP have no normalized actual metrics.
Only PostgreSQL's explicitly supplied top-level Execution Time is treated as whole-query time.

## Version 1 cardinality formulas

When comparable estimated E and actual A counts exist:

- Signed row estimation error = A - E.
- E > 0: ratio = A / E, rounded to six decimal places.
- E = 0 and A = 0: BOTH_ZERO, ratio 1, error 0.
- E = 0 and A > 0: ZERO_ESTIMATE, ratio null, signed error A.
- Missing values, zero loops, parallel-aware/worker-bearing PostgreSQL nodes, or an unrepresentable
  ratio: NOT_EVALUATED; no non-finite ratio is emitted.

Counts are compared per invocation, never multiplied by loops. The mismatch rule uses the
reported ratio at least 10 or at most 0.1, or ZERO_ESTIMATE. Early termination, LIMIT and partial
execution can explain mismatches; findings require investigation rather than assert stale statistics.
Parallel worker metadata remains available for manual interpretation.

Large scans (10,000 estimated rows), high volume (100,000 rows), repeated inner loops or
materialization (1,000 loops), and depth above 24 are versioned review heuristics. They are not
calibrated execution costs. See the [rule catalog](PHASE_10_3_DIAGNOSTIC_RULES.md).
