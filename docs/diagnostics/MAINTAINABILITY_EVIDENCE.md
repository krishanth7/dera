# Maintainability Evidence Model

## Evidence Structure

Every maintainability finding encapsulates verifiable `DiagnosticEvidence` grounding the diagnostic in observed metadata:

```python
@dataclass(frozen=True)
class DiagnosticEvidence:
    object_id: str
    field_name: str
    observed_value: Any
    expected_value: Any
    message: str
    provenance_reference: str | None = None
    context_data: dict[str, Any] = field(default_factory=dict)
```

## Evidence Fields per Rule

| Rule ID | `field_name` | `observed_value` | `expected_value` | Context Keys |
| :--- | :--- | :--- | :--- | :--- |
| `DERA-MNT-001` | `"column_count"` | Integer column count | `"< {threshold}"` | `table_id`, `table_name`, `namespace`, `threshold` |
| `DERA-MNT-002` | `"nullability_ratio"`| Float ratio | `"< {threshold}"` | `table_id`, `nullable_column_count`, `column_count` |
| `DERA-MNT-003` | `"table_name"` / `"column_name"` | String identifier | `"Matches profile '{profile}'"` | `configured_profile`, `deviating_identifier` |
| `DERA-MNT-004` | `"table_name"` / `"column_name"` | String keyword | `"Non-reserved identifier"` | `engine`, `reserved_keyword` |
| `DERA-MNT-005` | `"object_share_ratio"` | Float ratio | `"< 0.9"` | `dominant_namespace`, `empty_namespaces` |
| `DERA-MNT-006` | `"total_degree"` | Integer degree | `"< {threshold}"` | `in_degree`, `out_degree`, `total_degree` |
| `DERA-MNT-007` | `"complex_scc_membership"` | String SCC description | `"Acyclic or simple component"` | `scc_id`, `member_count`, `cycles` |
| `DERA-MNT-008` | `"lob_column_count"` | Integer LOB count | `"< {threshold}"` | `lob_columns`, `lob_count`, `threshold` |

## Stable Finding Fingerprints

Fingerprints are computed cryptographically using SHA-256 over:
- Rule ID.
- Rule Version.
- Target Object Canonical ID.
- Field Name.
- Observed Metric Value.
- Configured Threshold.

Volatile run timestamps and execution durations are excluded from structural fingerprint calculations.
