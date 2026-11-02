# Phase 10.3 Plan Rule Catalog

All severities are INFORMATIONAL. Ordering is rule ID then stable node ID. Findings retain
observations and limitations, never automatic remediation or unsupported speed claims.

| ID | Trigger | Investigation |
|---|---|---|
| PLAN001 | SCAN with at least 10,000 estimated rows | Review selectivity and existing index options; sequential scan may be optimal |
| PLAN003 | At least 100,000 estimated rows | Review required volume and filtering |
| PLAN004 | Comparable ratio >=10 or <=0.1, or zero estimate with positive actual | Investigate estimates, correlation and early termination |
| PLAN005 | PostgreSQL Sort Space Type=Disk | Review sort input and memory constraints |
| PLAN006 | Explicit temporary-table flag, MariaDB temporary_table or SQLite TEMP B-TREE | Inspect temporary storage |
| PLAN007 | Nested-loop inner child with at least 1,000 actual loops | Review repeated access and selectivity |
| PLAN008 | Explicit Hash Batches >1 | Inspect hash batching and memory context |
| PLAN010 | Materialize/Memoize with at least 1,000 actual loops | Inspect reuse; loops do not prove repeated underlying computation |
| PLAN011 | First node at depth 25 on each branch | Review structural nesting |
| PLAN015 | Node lacks normalized estimated rows or inclusive cost | Explain metric coverage; no actual measurement is fabricated |
| PLAN016 | Unknown operation or unrecognized nested structure | Inspect preserved native metadata; report PARTIAL |

PLAN015/016 are structural limitations. Other findings are review heuristics with evidence.
Recommendations retain finding, node and rule references, manual-review requirement, evidence,
a qualified expected benefit and limitations. No CREATE INDEX statement or SQL rewrite is emitted.

Candidate PLAN002, PLAN009, PLAN012, PLAN013 and PLAN014 are deferred: catalog/index absence,
join-order optimality, materialized intermediate cardinality and parallel overhead cannot be
established reliably from all supported imported formats. No rule asserts an unused or missing
index without authoritative catalog and workload evidence. A filesort indicator alone is not a
measured disk spill. Recommendations do not promise speed improvements.
