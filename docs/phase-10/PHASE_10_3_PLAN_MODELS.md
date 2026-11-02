# Phase 10.3 Canonical Plan Models

All public contracts extend Phase 10.1's frozen, extra-forbidden Pydantic model.
Model, parser and rule versions are `1.0.0`.

| Contract | Responsibility |
|---|---|
| ExecutionPlan | Status, dialect, flat nodes, roots, summary, findings, recommendations, provenance, associated SQL report, fingerprint |
| ExecutionPlanNode | Stable preorder/input-order node ID, parent, depth, operation, ordered child IDs, relation, estimates, actuals, native metadata JSON |
| PlanOperation | Typed canonical operation enumeration including UNKNOWN |
| PlanRelation | Reported name/schema/alias/index and explicit covering indication |
| PlanCostEstimate | Nullable startup/total/rows/width/filter, engine-specific units and semantics |
| PlanActualMetrics | Nullable rows/loops/time, explicit semantic labels, ratio/error/case |
| PlanDiagnostic | Stable rule/finding/node IDs, Phase 8 severity, evidence, investigation, limitations and runtime-verification requirement |
| PlanRecommendation | Stable ID, finding/rule/node references, evidence, suggested action, qualified benefit and manual review |
| PlanSummary | Counts/depth, actual-metric availability, root cost, execution time, operation counts, highest inclusive cost nodes |
| PlanProvenance | Imported-unverified acquisition, canonical input hash, format and versions |

Null means unavailable. Zero is preserved as zero. Native fields are not transformed into
measurements unless their documented semantics are supported. Native JSON can include sensitive
filter literals: it is returned only to the authorized caller and displayed as escaped text.

Node IDs are `n0000`, `n0001`, etc. Child ordering remains meaningful. SQLite IDs are mapped
without discarding original native rows. JSON object keys serialize in sorted order; arrays preserve
order. Duplicate input keys, non-finite numbers and invalid references are rejected.

The report fingerprint is SHA-256 of `DERA:EXECUTION-PLAN:V1\n` plus canonical report JSON,
excluding the fingerprint field itself. It includes native metadata, all version identifiers and
optional SQL diagnostic results. Equivalent input key ordering is normalized where structural
object traversal permits it. Whitespace is excluded from the canonical input hash; array order
is deliberately retained. No time-dependent fields or random IDs enter analysis output.
