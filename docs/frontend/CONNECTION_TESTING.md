# Connection Testing Specification

**Document Reference**: `docs/frontend/CONNECTION_TESTING.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Connection Diagnostic Probing

DERA provides deterministic connection testing without performing metadata extraction or persisting unvalidated credentials.

### Testing Modalities

1. **Pre-Save Diagnostic Probe (`POST /api/v1/connections/test`)**:
   - Executes an ephemeral probe using form values before creating a connection.
   - Evaluates TCP handshake, TLS negotiation, authentication credentials, and database selection.
   - Never saves credentials to the database if the test fails.

2. **Persisted Connection Test (`POST /api/v1/workspaces/{workspace_id}/connections/{connection_id}/test`)**:
   - Uses credentials stored in the backend vault.
   - Updates the live status badge (`connected` or `failed`) with timestamp and round-trip latency.

---

## 2. Diagnostic Result Telemetry

The frontend renders diagnostic feedback with granular error categorizations:

| Diagnostic Status | Cause | UI Presentation |
|---|---|---|
| `success` | Valid handshake, auth, and read-only access | Green badge with measured latency in milliseconds |
| `auth_failed` | Invalid username, password, or role permissions | Yellow warning alert with guidance on database grants |
| `network_error` | Connection refused, timeout, or DNS resolution failure | Red error alert with host/port verification guidance |
| `tls_error` | Certificate validation failure or SSL mismatch | Red error alert highlighting TLS requirement |
| `path_error` | SQLite file not found or path containment violated | Red alert displaying directory containment restrictions |

---

## 3. Non-Blocking Execution

Connection tests run asynchronously with explicit loading indicators. The user may cancel an in-flight test or adjust configuration parameters immediately upon failure.
