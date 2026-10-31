# Maintainability Thresholds & Configuration

## Configuration Mechanics

All maintainability thresholds are configurable via `DiagnosticEngineConfig.rule_thresholds`. All threshold inputs are strictly validated: negative or nonsensical values are rejected during initialization.

```python
config = DiagnosticEngineConfig(
    rule_thresholds={
        "max_table_width": 30,
        "review_table_width": 50,
        "elevated_table_width": 100,
        "max_nullability_ratio": 0.50,
        "elevated_nullability_ratio": 0.75,
        "naming_profile": "snake_case",
        "max_namespace_imbalance_ratio": 0.90,
        "max_structural_coupling_degree": 12,
        "elevated_coupling_degree": 24,
        "min_complex_scc_size": 3,
        "max_lob_columns_per_table": 4,
        "elevated_lob_columns_per_table": 8,
    }
)
```

## Configurable Thresholds Table

| Key | Default | Type | Description |
| :--- | :--- | :--- | :--- |
| `max_table_width` | 30 | `int` | Column count baseline threshold (`INFORMATIONAL`) |
| `review_table_width` | 50 | `int` | Column count review threshold (`LOW`) |
| `elevated_table_width` | 100 | `int` | Column count elevated threshold (`MEDIUM`) |
| `max_nullability_ratio` | 0.50 | `float` | Table nullability ratio baseline (`INFORMATIONAL`) |
| `elevated_nullability_ratio` | 0.75 | `float` | Table nullability ratio elevated (`LOW`) |
| `naming_profile` | `"snake_case"` | `str` | Profile: `snake_case`, `camelCase`, `PascalCase`, etc. |
| `max_namespace_imbalance_ratio` | 0.90 | `float` | Max concentration in single namespace (`INFORMATIONAL`) |
| `max_structural_coupling_degree`| 12 | `int` | Total relational degree baseline (`LOW`) |
| `elevated_coupling_degree` | 24 | `int` | Total relational degree elevated (`MEDIUM`) |
| `min_complex_scc_size` | 3 | `int` | Minimum tables in cyclic SCC (`LOW`) |
| `max_lob_columns_per_table` | 4 | `int` | LOB columns per table baseline (`INFORMATIONAL`) |
| `elevated_lob_columns_per_table`| 8 | `int` | LOB columns per table elevated (`LOW`) |
