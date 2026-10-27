# Stable Object Identity Design

**Subsystem:** `dera.metadata.identity`  

---

## 1. Identity Motivation

Relational database catalogs use transient, engine-specific internal identifiers (such as PostgreSQL `oid` or SQLite rowids) that change when a table is dumped, restored, or re-created.

DERA creates **reproducible, cryptographic, deterministic ObjectIds** that remain identical across consecutive inspection runs as long as the underlying schema definition is unchanged.

---

## 2. Formulation & Algorithm

Every object ID is generated via a length-prefixed canonical frame hashed with SHA-256:

```text
FRAME = "v1"
        + "|" + len(engine) + ":" + engine
        + "|" + len(workspace_id or "") + ":" + (workspace_id or "")
        + "|" + len(connection_id or "") + ":" + (connection_id or "")
        + "|" + len(namespace or "") + ":" + (namespace or "")
        + "|" + len(object_kind.value) + ":" + object_kind.value
        + "|" + len(parent_id or "") + ":" + (parent_id or "")
        + "|" + len(native_name) + ":" + native_name
        [+ "|" + "terms:" + len(terms) + "[" + sum(len(t) + ":" + t) + "]"]

DIGEST = SHA256(FRAME)[0:24]
OBJECT_ID = "dera:" + object_kind.value + ":" + DIGEST
```

### Format
`dera:<object_kind>:<24_hex_digits>`

### Example Identifiers
- Table: `dera:table:a1b2c3d4e5f60718293a4b5c`
- Column: `dera:column:f1e2d3c4b5a69788796a5b4c`
- Primary Key: `dera:primary_key:1a2b3c4d5e6f708192a3b4c5`

---

## 3. Delimiter Injection Defense

Naive delimiter concatenation (e.g. `engine + "_" + name`) is vulnerable to injection attacks where tokens containing underscores collide (`a` + `bc` vs `ab` + `c`). Length-prefixed framing guarantees that each token boundary is unambiguous and collision-resistant.
