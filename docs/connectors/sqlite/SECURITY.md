# DERA SQLite Connector Security Model

## Multi-Layer Read-Only Defense in Depth

The SQLite connector enforces 7 distinct defensive layers to guarantee zero mutation of customer databases:

1. **Layer 1: Protocol Interface Invariants**
   The `DatabaseConnector` interface defines strictly read-only catalog discovery methods. Methods such as `execute_sql`, `mutate`, `drop_table`, or `insert` do not exist.
2. **Layer 2: Pre-Reviewed Query Inventory**
   Only verified catalog introspection queries and safe PRAGMAs (`PRAGMA table_xinfo`, `PRAGMA foreign_key_list`, `PRAGMA index_xinfo`, `PRAGMA database_list`) are constructed and executed. All identifiers are safely escaped with double quotes.
3. **Layer 3: SQLite URI `mode=ro` Enforcement**
   Every connection URI is constructed using `file:/canonical/path?mode=ro`. The SQLite C runtime rejects write transactions at the VFS storage layer.
4. **Layer 4: Runtime PRAGMA Locking**
   Immediately after opening any connection, the connector executes:
   ```sql
   PRAGMA query_only = ON;
   PRAGMA busy_timeout = 5000;
   ```
5. **Layer 5: Filesystem Permissions & Confinement**
   Target database files must reside within explicit workspace-approved storage roots. Directory traversal sequences (`..`), system directories, and unauthorized symlinks are rejected.
6. **Layer 6: Extension & Attachment Restrictions**
   SQLite dynamic extension loading (`load_extension`) is disabled. The connector executes no `ATTACH DATABASE` statements, preventing filesystem traversal via arbitrary database attachments.
7. **Layer 7: Automated Conformance & Security Verification**
   CI continuously verifies that `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, and `ALTER` statements fail unconditionally against real test databases.
