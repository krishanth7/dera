# Maintainability Metrics Catalog

## Formal Specification

Every maintainability metric in DERA adheres to strict specifications declaring stable identifier, mathematical formula, measurement unit, structural scope, engine applicability, limitations, and semantic version.

| Metric ID | Name | Formula | Unit | Scope | Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `MNT-MET-001` | Table Column Width | $\text{count}(\text{columns})$ | count | `TABLE` | Unbounded analytical marts require custom thresholds |
| `MNT-MET-002` | Column Nullability Ratio | $\frac{\text{nullable\_columns}}{\text{total\_columns}}$ | ratio | `TABLE` | Evaluated only for tables with $\ge 5$ columns |
| `MNT-MET-003` | Naming Convention Compliance | $\frac{\text{compliant\_identifiers}}{\text{total\_identifiers}}$ | ratio | `SCHEMA` | Quoted names stripped; case-folding applied |
| `MNT-MET-004` | Namespace Object Concentration | $\max_{ns} \left( \frac{\text{tables in } ns}{\text{total tables}} \right)$ | ratio | `DATABASE` | Inapplicable to single-schema databases |
| `MNT-MET-005` | Relational Degree Centrality | $\text{in\_degree} + \text{out\_degree}$ | edges | `TABLE` | Junction tables naturally have higher degree |
| `MNT-MET-006` | Complex Cyclic SCC Size | $\text{count}(\text{tables in cyclic SCC})$ | count | `RELATIONSHIP` | Requires complete foreign key metadata |
| `MNT-MET-007` | LOB Column Concentration | $\text{count}(\text{LOB columns})$ | count | `TABLE` | Engine-specific native data types |
| `MNT-MET-008` | Average Columns Per Table | $\frac{\text{total columns}}{\text{total tables}}$ | columns | `SCHEMA` | Global aggregate indicator |

## Maintainability Metric Scope

- `DATABASE`: Evaluates inter-namespace distribution and multi-schema structures.
- `SCHEMA`: Evaluates aggregates across tables, views, and naming profiles.
- `TABLE`: Evaluates individual table width, nullability, and storage types.
- `COLUMN`: Evaluates individual column data types and identifiers.
- `RELATIONSHIP`: Evaluates graph coupling and cyclic dependency components.
