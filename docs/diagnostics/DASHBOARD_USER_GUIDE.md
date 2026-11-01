# Diagnostics Dashboard User Guide

## User Overview

The Diagnostics Dashboard enables database engineers, architects, and reliability specialists to inspect database schema health, identify structural defects, evaluate maintainability bottlenecks, and review engineering recommendations.

## Navigating the Dashboard

1. **Accessing the Route**: Select **Diagnostics** in the application sidebar or navigate to `/app/diagnostics`.
2. **Reviewing Top-Level Metrics**:
   - **Total Findings**: Aggregate issue count across all evaluated rules.
   - **Critical / High / Medium / Low / Informational**: Findings categorized by conservative severity.
   - **Suppressed**: Findings exempted by engineering governance policies.
   - **Rules Run**: Total active diagnostic rules evaluated against the schema.
3. **Filtering and Searching**:
   - Use the search bar to query findings by title, rule ID (e.g., `DERA-IDX-001`), or table name (e.g., `public.users`).
   - Filter by severity level or engineering category (Indexes, Constraints, Relationships, Maintainability).
   - Toggle between active findings and suppressed exemptions.
4. **Inspecting Finding Details**:
   - Click on any finding row or press `Enter` to open the Finding Details drawer.
   - Review the **Severity Rationale** explaining why the severity was assigned.
   - Inspect the **Advisory Recommendation** detailing suggested remediation, preconditions, risk factors, and verification steps.
   - Examine **Verified Evidence** records showing observed catalog values versus expected norms.
5. **Managing Suppressions**:
   - Click **Exempt Finding** to record a justified, time-bounded suppression.
   - Enter mandatory justification and select an expiration window (7 days to 1 year).
   - Click **Revoke Exemption** to immediately reactivate the finding in compliance reports.
