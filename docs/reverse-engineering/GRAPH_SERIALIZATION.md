# Graph Serialization & Canonical Fingerprinting

## 1. Serialization Architecture

Graph serialization in [`serialization.py`](file:///packages/core/src/dera/reverse_engineering/graph/serialization.py) provides deterministic, auditable JSON serialization and deserialization conforming to RFC 8785 (Canonical JSON principles).

Key guarantees:
1. **Sorted Keys**: Dictionary keys are sorted lexicographically at all nesting depths.
2. **Compact Formatting**: No superfluous whitespace (`separators=(",", ":")`).
3. **ISO UTC Dates**: Timestamps serialize in ISO 8601 UTC representation (`YYYY-MM-DDTHH:MM:SSZ` or with microsecond precision).
4. **Deterministic Collections**: Nodes, edges, column pairs, and unresolved references are sorted deterministically prior to dumping.

---

## 2. SHA-256 Content Fingerprint

Every `ForeignKeyGraph` instance can produce a deterministic SHA-256 fingerprint:

```python
fingerprint: str = graph.compute_hash()
# Example: "8f4a132c...b129"
```

### Invariant:
$$\text{Graph}_A = \text{Graph}_B \iff \text{hash}(\text{Graph}_A) = \text{hash}(\text{Graph}_B)$$

Even if nodes or constraints were presented in different order during database introspection, the canonical ordering and JSON dumping ensures bit-for-bit hash equality.

---

## 3. Serialization Payload Limits

To prevent memory exhaustion attacks or Denial of Service via malicious schema payloads, [`GraphResourceLimits`](file:///packages/core/src/dera/reverse_engineering/graph/limits.py) enforces:

- `max_serialized_bytes = 10_000_000` (10 MB default)

Attempting to serialize or deserialize a payload exceeding this limit raises [`GraphResourceLimitError`](file:///packages/core/src/dera/reverse_engineering/graph/errors.py).

---

## 4. Deserialization Safety

The deserializer `deserialize_graph_from_json(json_str)`:
1. Validates payload size before JSON parsing.
2. Forbids unknown fields (`extra="forbid"` on all models).
3. Re-validates node uniqueness, edge uniqueness, endpoint existence, and contract version (`phase-6.3-foreign-key-graph-v1`).
4. Reconstructs identical frozen instances that round-trip with matching SHA-256 fingerprints.
