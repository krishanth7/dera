# DERA Transaction Policy

## 1. Core Transaction Guarantees

1. **Explicit Boundaries**: All database mutations must occur within explicit transaction boundaries.
2. **Automatic Rollback**: Any unhandled exception raised within a transaction boundary immediately triggers an asynchronous rollback.
3. **No Implicit Commits**: DERA sessions have `autocommit=False`. Operations are committed only when explicitly requested via `session.commit()` or upon clean exit from `transaction_scope`.

---

## 2. Using `transaction_scope`

The `dera_api.db.session.transaction_scope` context manager provides safe, clean transaction management:

```python
from dera_api.db.session import transaction_scope
from dera_api.repositories.base import PlatformMetadataRepository

async def update_platform_setting(session, key: str, value: str):
    async with transaction_scope(session):
        repo = PlatformMetadataRepository(session)
        await repo.set_value(key, value)
        # Atomically commits upon exiting the block
```

---

## 3. Nested Transactions & Savepoints

When `transaction_scope` is invoked on a session that already has an active transaction, it automatically establishes a **savepoint** via `session.begin_nested()`. If an exception occurs inside the inner block, only the inner savepoint is rolled back, leaving outer changes intact unless re-raised.
