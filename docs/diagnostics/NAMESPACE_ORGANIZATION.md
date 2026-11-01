# Namespace Organization & Imbalance Diagnostics (DERA-MNT-005)

## Overview

In multi-tenant or multi-schema database engines (PostgreSQL, MySQL, MariaDB), namespaces (schemas) logically partition database entities into domain boundaries.

When a database declares multiple namespaces but concentrates nearly all tables into a single schema while others remain empty or vestigial, it indicates:
1. Monolithic schema design with missing bounded contexts.
2. Stale or abandoned schemas left behind from incomplete migrations.
3. Undecomposed microservice boundaries.

Rule `DERA-MNT-005` audits namespace distributions.

## Evaluation Semantics

1. **Single-Namespace Exemption**: Databases with only 1 schema (such as SQLite or single-schema databases) return `NOT_APPLICABLE`.
2. **Minimum Table Volume**: Schemas with fewer than 10 tables return `PASS` to prevent false positive alerts during early prototyping.
3. **Imbalance Metric**:
   $$\text{imbalance\_ratio} = \max_{ns} \left( \frac{\text{tables in } ns}{\text{total database tables}} \right)$$
   When $\text{imbalance\_ratio} \ge 0.90$ across $\ge 2$ namespaces, a finding is emitted.
4. **Empty Namespaces**: Empty namespaces are collected and reported in `context_data["empty_namespaces"]`.

## Severity Policy

Namespace imbalance is classified as `INFORMATIONAL`. Partitioning across namespaces is an architectural choice and does not constitute a database fault.
