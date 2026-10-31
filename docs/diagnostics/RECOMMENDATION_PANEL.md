# Recommendation Panel Specification

## Overview

The Recommendation Panel presents deterministic engineering actions generated from versioned recommendation templates.

## Structure and Content

- **Advisory Banner**: Prominently highlights that DERA is read-only and never executes mutations automatically.
- **Title & Suggested Action**: Exact steps required to resolve the structural discrepancy.
- **Risk Considerations**: Potential pitfalls, lock contention risks, or API regressions.
- **Verification Steps**: Concrete queries (e.g., `EXPLAIN ANALYZE` or null checks) to validate remediation in pre-production environments.
