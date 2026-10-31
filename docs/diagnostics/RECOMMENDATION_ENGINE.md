# Recommendation Engine Specification

## Overview

The DERA Recommendation Engine generates deterministic, actionable engineering advice for each diagnostic finding. The engine enforces strict safety guarantees: recommendations are purely advisory, never execute database mutations automatically, and never propose destructive schema operations without explicit multi-step verification procedures.

## Architecture

The engine transforms verified findings into structured recommendations through three layers:

```text
Diagnostic Finding -> Template Selector -> Safety Validator -> Structured Recommendation
```

1. **Template Selection**: Locates the versioned recommendation template matching the finding's `rule_id` in the `RECOMMENDATION_CATALOG`.
2. **Context Substitution**: Populates placeholders using verified evidence values (object names, column lists, metric values).
3. **Safety Validation**: Evaluates generated text against the Safety Directive:
   - Prohibits destructive keywords (`DROP TABLE`, `TRUNCATE`, `rm -rf`, `DELETE CASCADE`).
   - Ensures verification steps and risk considerations are populated.
   - Flags advisory nature.

## Recommendation Safety Guardrails

- **Advisory Only**: DERA never executes generated SQL statements.
- **Index Recommendations**: Recommends reviewing query patterns and verifying index usage statistics before dropping or creating indexes.
- **Foreign Key Indexing**: Advises evaluating query workloads before adding secondary indexes on high-churn foreign key columns.
- **Schema Normalization**: Offers guidance on decomposition patterns without auto-generating migration scripts.
