# Diagnostic Evidence Model for Indexes and Constraints

## 1. Evidence Architecture
In accordance with DERA Phase 8.1, all Phase 8.2 diagnostic rules generate structured `DiagnosticEvidence` objects rather than generic error strings.

```python
@dataclass(frozen=True)
class DiagnosticEvidence:
    object_id: str
    field_name: str
    observed_value: Any
    expected_value: Any | None = None
    message: str = ""
    provenance_reference: str | None = None
    context_data: dict[str, Any] = field(default_factory=dict)
```

## 2. Redaction & Credential Sanitization
All values passed to `DiagnosticEvidence` are sanitized via `sanitize_value()`, redacting passwords, tokens, API keys, and connection credentials from `context_data`.

## 3. Evidence Payload Examples
- **Duplicate Indexes (`DERA-IDX-001`)**:
  - `field_name`: `"index_definition"`
  - `observed_value`: `"Identical BTREE index definition on ('email')"`
  - `context_data`: Primary index ID/name, duplicate index ID/name, ownership descriptions.
- **Foreign Key Coverage (`DERA-IDX-003`)**:
  - `field_name`: `"fk_index_coverage"`
  - `observed_value`: `"No non-partial leading-prefix index"`
  - `context_data`: Foreign key columns, referenced table, existing candidate partial indexes.
