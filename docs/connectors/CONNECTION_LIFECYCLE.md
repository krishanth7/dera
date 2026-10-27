# Connection Lifecycle & State Machine

## Finite State Machine

Connection lifecycles are governed by `ConnectionLifecycle` (`packages/connectors/src/dera_connectors/lifecycle.py`):

```
[CREATED] ----> [CONNECTING] ----> [CONNECTED] ----> [CLOSING] ----> [CLOSED]
                   |                   |
                   +---> [FAILED] <----+
                           |
                           +---> [CLOSING] ----> [CLOSED]
```

## Lifecycle States

- `CREATED`: Adapter instantiated; configuration validated; no network socket opened.
- `CONNECTING`: Socket connection or authentication in progress.
- `CONNECTED`: Active connection; session initialized with read-only transaction parameters.
- `FAILED`: Connection or authentication failed; failure reason recorded; awaiting cleanup.
- `CLOSING`: Teardown initiated; sockets closing, sessions being released.
- `CLOSED`: Terminal state; all driver resources freed.

## Safety Principles

1. **Terminal Immutability:** Closed connections cannot be reconnected. New operations require creating a fresh connector instance.
2. **Failure Cleanup:** Connectors in the `FAILED` state must be cleanly transitioned to `CLOSED` via `await connector.close()`.
3. **Idempotent Close:** Calling `close()` on an already closed connector is a safe no-op.
