# Evidence Traceability Specification

## Overview

DERA Phase 8.5 enforces complete evidence traceability for every diagnostic finding. A finding cannot exist without auditable evidence pointing to verified canonical schema objects, column definitions, constraints, indexes, or explicit metadata limitations.

## Evidence Hierarchy and Types

Evidence items in DERA are strongly typed via `DiagnosticEvidenceType`:

| Evidence Type | Semantic Role | Target Reference |
| :--- | :--- | :--- |
| `CANONICAL_OBJECT` | Identifies the primary database entity affected | Canonical Object ID (`schema.table`) |
| `COLUMN_REFERENCE` | Identifies specific columns involved in the finding | Fully qualified column name |
| `CONSTRAINT_REFERENCE` | References primary keys, foreign keys, or check constraints | Constraint name and table |
| `INDEX_REFERENCE` | References secondary, unique, or partial indexes | Index name and definition |
| `GRAPH_EDGE` | Traces relationship or dependency connections | Source and target node IDs |
| `METRIC_OBSERVATION` | Quantifies structural metrics (fan-in, width, depth) | Observed numerical value |
| `THRESHOLD_COMPARISON`| Documents comparison against configured threshold | `{observed: X, threshold: Y}` |
| `METADATA_CAPABILITY` | Explicitly states connector capabilities or limitations | Feature flag or capability enum |
| `SNAPSHOT_REFERENCE` | Links finding to the exact schema snapshot analyzed | Snapshot ID and hash |
| `PROVENANCE_REFERENCE`| Captures extraction timestamp and engine details | Engine name and connector version |

## Evidence Traceability Matrix

The diagnostic evaluator constructs an Evidence Traceability Matrix linking:
- Finding ID -> Verified Canonical Object ID
- Finding ID -> Supporting Evidence Items
- Supporting Evidence Items -> Verified Canonical Model Elements
- Any unresolved references are explicitly flagged with `unresolved=True`
