# Snapshot Identity Model

## 1. Identity Triad

DERA establishes three distinct and independent identity concepts:

```text
┌────────────────────────────────────────────────────────┐
│ 1. Snapshot Record ID (`snapshot_id`)                  │
│    Format: `snap_<32-hex-chars>`                       │
│    Scope:  Unique per snapshot capture event           │
└────────────────────────────────────────────────────────┘
                           ▲
                           │ captures
                           ▼
┌────────────────────────────────────────────────────────┐
│ 2. Structural Fingerprint (`fingerprint`)              │
│    Format: `<64-hex-chars>` (SHA-256)                  │
│    Scope:  Content-addressable structural equivalence   │
└────────────────────────────────────────────────────────┘
                           ▲
                           │ describes
                           ▼
┌────────────────────────────────────────────────────────┐
│ 3. Database Identity (`database_id`)                   │
│    Format: `dera:database:<object-id>`                 │
│    Scope:  Source database instance identity           │
└────────────────────────────────────────────────────────┘
```

---

## 2. Snapshot ID Format

Snapshot record identifiers are generated via `generate_snapshot_id()`:
- Prefix: `snap_`
- Entropy: 128 bits of cryptographic randomness (32 hexadecimal characters from `secrets.token_hex(16)`)
- Total length: 37 characters
- Regular expression: `^snap_[0-9a-f]{32}$`

Example:
```text
snap_794632676cf14110808621db66f099ba
```

---

## 3. Disambiguation Principles

1. **Two captures of the same database with identical schemas**:
   - Distinct `snapshot_id` (e.g. `snap_1111...` and `snap_2222...`)
   - Identical `fingerprint` (e.g. `0f37c68e...`)
   - Identical `database_id`

2. **Two different databases (e.g. dev and prod) with identical schemas**:
   - Distinct `snapshot_id`
   - Identical `fingerprint`
   - Distinct `database_id`

3. **Two captures of the same database after a DDL migration**:
   - Distinct `snapshot_id`
   - Distinct `fingerprint`
   - Identical `database_id`

Fingerprints must **never** be used as a substitute for tenant or workspace authorization.
