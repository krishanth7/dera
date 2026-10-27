# Database Identifier Normalization Rules

**Subsystem:** `dera.metadata.identifiers`  

---

## 1. Dialect Quoting & Case Semantics

Different database engines enforce distinct rules regarding case sensitivity and quotation:

| Engine | Unquoted Casing Behavior | Quoted Syntax | Case Sensitivity |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | Folds to lowercase | `"name"` | Case-sensitive if quoted; folded if unquoted |
| **SQLite** | Preserves case in catalog | `"name"` or `[name]` | Case-insensitive ASCII lookup; case-preserving storage |
| **MySQL** | Dependent on `lower_case_table_names` | `` `name` `` | Tables depends on OS/config; columns case-insensitive |
| **MariaDB** | Dependent on `lower_case_table_names` | `` `name` `` | Same as MySQL |

---

## 2. DERA Identifier Fidelity

- **Zero Global Lowercasing:** DERA preserves the exact declared casing in catalog metadata (`Identifier.canonical_name`).
- **Engine Lookup Key:** For case-insensitive index/relationship mapping, `Identifier.lookup_key()` applies dialect-specific case folding without overwriting the displayed or stored identifier.
- **Unquoting:** Enclosing quotation marks (`"`, `` ` ``, `[]`) are stripped while setting `is_quoted = True` and recording `quote_char`.
