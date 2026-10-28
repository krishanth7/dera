# Deterministic Cryptographic Fingerprints

## 1. Cryptographic Primitive

DERA employs cryptographic SHA-256 (FIPS 180-4) as its primary fingerprint digest function.

The structural fingerprint represents the immutable digest of all schema-defining elements of a database at a specific snapshot point.

---

## 2. Domain Separation

To prevent length extension attacks, cross-protocol collision attacks, or accidental equivalence with other hash uses (such as table-level hashes or ObjectIds), DERA enforces cryptographic domain separation.

### Domain Prefix
```text
DERA:SCHEMA:STRUCTURAL:V1\n
```

### Hashing Formula
```text
FINGERPRINT = SHA256( "DERA:SCHEMA:STRUCTURAL:V1\n" || RFC8785_CANONICAL_BYTES(payload) )
```

```python
import hashlib

def compute_structural_fingerprint(payload: SnapshotStructuralPayload) -> str:
    canonical_bytes = serialize_structural_payload_to_bytes(payload)
    hasher = hashlib.sha256()
    hasher.update(b"DERA:SCHEMA:STRUCTURAL:V1\n")
    hasher.update(canonical_bytes)
    return hasher.hexdigest()
```

---

## 3. Structural Scope

The structural fingerprint covers exclusively fields in `SnapshotStructuralPayload`:
- Database identity and engine
- All namespaces, tables, columns, constraints, and indexes
- View expressions and trigger bindings
- Verified relationship edges and dependency metrics
- Metadata completeness flag

### Excluded Scope (Envelope)
The following fields do **not** affect the structural fingerprint:
- Snapshot record ID (`snapshot_id`)
- Capture timestamp (`capture_timestamp`)
- Workspace ID (`workspace_id`)
- Requester ID (`requester_id`)
- Storage location URI
- Custom user tags

---

## 4. Cryptographic Test Vectors

Reviewed reference vectors for the `DERA:SCHEMA:STRUCTURAL:V1` contract:

| Fixture | Canonical Bytes | Expected SHA-256 Digest |
| :--- | :--- | :--- |
| `empty_db` | 349 | `5a341218a5a6965a5c1c4e03720510e0d67d558e56abbb69528634b91017d8df` |
| `single_tbl_db` | 1668 | `0f37c68ee6534cb98f678e6bb57331ed09b898419546a06b25d2113804f12680` |
| `composite_db` | 3211 | `e63982b1804665c416a0b71d6d129bd97b222ec70eedc616dabef0640a739eb9` |
| `unicode_db` | 1463 | `d70235206edeebcfc5fb2566ae09162eb9c897d3c9c98ec10e87cbe399246de4` |
