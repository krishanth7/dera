# Graph Validation & Referential Integrity

## 1. Validation Architecture

Validation is executed by [`validate_foreign_key_graph`](file:///packages/core/src/dera/reverse_engineering/graph/validation.py) during graph construction or on-demand.

The validator inspects structural, referential, and workspace integrity, emitting structured [`GraphValidationFinding`](file:///packages/core/src/dera/reverse_engineering/graph/validation.py) records.

```python
class ValidationSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

class GraphValidationFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    severity: ValidationSeverity
    message: str
    object_id: ObjectId | None = None
    details: dict[str, Any] = Field(default_factory=dict)
```

---

## 2. Validation Rules

| Rule ID | Severity | Description |
| :--- | :--- | :--- |
| `NODE_UNIQUE_ID` | `ERROR` | Duplicate `table_id` detected across table nodes. |
| `EDGE_UNIQUE_ID` | `ERROR` | Duplicate `edge_id` detected across foreign key edges. |
| `EDGE_SOURCE_EXISTS` | `ERROR` | Edge declares a `source_table_id` that does not exist in nodes. |
| `EDGE_TARGET_EXISTS` | `ERROR` | Edge declares a `target_table_id` that does not exist in nodes. |
| `EDGE_COLUMN_PAIRS_NON_EMPTY` | `ERROR` | Edge contains zero column pair mappings. |
| `EDGE_COLUMN_COUNT_MISMATCH` | `ERROR` | Composite key has unequal source and target column counts. |
| `WORKSPACE_ISOLATION` | `ERROR` | Node or edge belongs to a workspace differing from the graph's scope. |
| `ADJACENCY_CONSISTENCY` | `ERROR` | An edge in the adjacency index does not exist in the graph's edge set. |
| `UNRESOLVED_REFERENCE` | `WARNING` | An unresolvable foreign key constraint was recorded. |
| `SELF_REFERENCE_INFO` | `INFO` | Informational record of a valid self-referencing relationship. |

---

## 3. Validation Modes

Validation behavior is governed by [`ValidationMode`](file:///packages/core/src/dera/reverse_engineering/graph/builder.py):

- **`ValidationMode.STRICT`**: Any `ERROR` severity finding raises [`GraphValidationError`](file:///packages/core/src/dera/reverse_engineering/graph/errors.py) immediately, aborting graph construction.
- **`ValidationMode.PERMISSIVE`**: All findings (including errors) are attached to `graph.validation_findings`. Missing targets are captured as `UnresolvedReference` objects rather than throwing fatal exceptions.

---

## 4. Referential Integrity Audit

The validation engine guarantees:
1. Every resolved edge connects two real, registered `TableNode`s.
2. Incomplete or restricted metadata is preserved rather than fabricated.
3. Workspace isolation prevents leakage across multi-tenant boundaries.
