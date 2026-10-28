# Cryptographic Snapshot Integrity Verification

## 1. Integrity Verification API

DERA provides a standalone, deterministic verification function:

```python
from dera.reverse_engineering.snapshots.integrity import verify_snapshot_integrity, IntegrityVerificationStatus

report = verify_snapshot_integrity(snapshot)
if not report.is_valid:
    print(f"Integrity check failed: {report.status} - {report.details}")
```

---

## 2. Verification Statuses

The `IntegrityVerificationStatus` enum details the exact outcome:

| Status | Meaning |
| :--- | :--- |
| `VALID` | Canonical serialization of `snapshot.payload` with domain separation matches `snapshot.fingerprint` bit-for-bit. |
| `MISMATCH` | Recomputed SHA-256 digest differs from recorded `snapshot.fingerprint`. Content was tampered with or corrupted. |
| `UNSUPPORTED_VERSION` | Format version or algorithm version is unrecognized by the current runtime. |
| `INVALID_PAYLOAD` | Payload violates structural bounds, contains non-finite numbers, or fails validation. |
| `VERIFICATION_ERROR` | Unexpected exception encountered during verification. |

---

## 3. Cryptographic Scope & Threat Model

### What SHA-256 Fingerprints Protect Against
1. **Accidental Bit Rot / Disk Corruption**: Bit flips in stored JSON files are immediately caught upon retrieval.
2. **Unauthorized Record Mutation**: Manual tampering or unauthorized modifications to columns, types, or constraints will fail fingerprint validation.
3. **Payload / Envelope Desynchronization**: Prevents associating an envelope with an altered payload.

### What Stored Fingerprints Do NOT Protect Against
A SHA-256 digest stored alongside the snapshot payload does **not** replace digital signatures (e.g. Ed25519 or HMAC) if an attacker has direct, arbitrary write access to the underlying storage volume and recalculates the hash.
Authenticity across untrusted transport boundaries requires signed attestations or storing fingerprints in a trusted tamper-evident ledger.
