# DERA Database Recovery & Incident Management

## 1. Truthful Recovery Guarantees

Executing `alembic downgrade` rolls back DDL schema objects (tables, columns, indexes), but **it does not restore deleted application data**. True disaster recovery depends on verified database backups and point-in-time recovery (PITR).

---

## 2. Recommended Backup Strategy

1. **Daily Full Logical/Physical Dumps**: Automated `pg_dump` or volume snapshots.
2. **Write-Ahead Log (WAL) Archiving**: Continuous WAL archiving for Point-In-Time Recovery (PITR).
3. **Pre-Migration Snapshot**: Before applying high-risk migrations, create an explicit database snapshot:

```bash
pg_dump -U dera_user -d dera_platform -Fc -f "pre_migration_$(date +%Y%m%d_%H%M%S).dump"
```

---

## 3. Forward-Fix Policy

When a migration introduces unexpected locking or performance regressions in production:

1. **Assess Data Integrity**: Determine whether data was transformed destructively.
2. **Prefer Forward-Fix**: For non-destructive issues, author and apply a new migration revision rather than downgrading live production schema.
3. **Rollback Protocol**: If rollback is necessary, ensure application processes are temporarily halted or placed into maintenance mode to prevent concurrent schema conflicts.
