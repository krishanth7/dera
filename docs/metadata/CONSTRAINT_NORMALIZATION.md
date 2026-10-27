# Constraint Normalization

**Subsystem:** `dera.metadata.models.constraint` & `relationship`  

---

## 1. Supported Constraints

- **Primary Key:** Explicit primary key constraint represented via `CanonicalConstraint(constraint_type=ConstraintType.PRIMARY_KEY)`.
- **Unique Constraints:** Non-primary unique constraints.
- **Check Constraints:** Row-level boolean invariant expressions.
- **Foreign Key Constraints:** Referential integrity links represented via `CanonicalForeignKey` with ordered `column_mappings`.

---

## 2. Unnamed Constraints & Synthetic Naming

Engines like SQLite and older MySQL versions frequently do not assign explicit catalog names to inline CHECK or UNIQUE constraints.
DERA generates deterministic, non-conflicting surrogate names:

- CHECK constraint: `_chk_<table_name>_<columns>`
- UNIQUE constraint: `_unq_<table_name>_<columns>`
- FOREIGN KEY constraint: `_fk_<table_name>_<columns>`

When a synthetic surrogate is generated, `is_synthetic_name = True` is recorded to clearly distinguish engine catalog identifiers from DERA surrogates.
