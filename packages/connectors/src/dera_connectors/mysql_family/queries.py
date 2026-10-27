"""DERA MySQL-Family Connectors — Pre-Reviewed Catalog Queries.

All queries against INFORMATION_SCHEMA are pre-approved, parameterized, and
deterministically ordered. Direct user-supplied SQL execution is strictly prohibited.
"""

from __future__ import annotations

# 1. Identity & Version Discovery
QUERY_IDENTITY = """
SELECT
    VERSION() AS server_version,
    @@version_comment AS version_comment,
    DATABASE() AS current_database,
    CURRENT_USER() AS current_user;
"""

# 2. Schema / Database Enumeration
QUERY_SCHEMAS = """
SELECT
    SCHEMA_NAME AS schema_name,
    DEFAULT_CHARACTER_SET_NAME AS character_set,
    DEFAULT_COLLATION_NAME AS collation_name
FROM INFORMATION_SCHEMA.SCHEMATA
WHERE SCHEMA_NAME NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
ORDER BY SCHEMA_NAME ASC;
"""

# 3. Table Enumeration
QUERY_TABLES = """
SELECT
    TABLE_SCHEMA AS schema_name,
    TABLE_NAME AS table_name,
    TABLE_TYPE AS object_type,
    ENGINE AS storage_engine,
    TABLE_COMMENT AS comment,
    TABLE_COLLATION AS collation_name,
    AUTO_INCREMENT AS auto_increment_val
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = %s
ORDER BY TABLE_SCHEMA ASC, TABLE_NAME ASC;
"""

# 4. Column Enumeration
QUERY_COLUMNS = """
SELECT
    TABLE_SCHEMA AS schema_name,
    TABLE_NAME AS table_name,
    COLUMN_NAME AS column_name,
    ORDINAL_POSITION AS ordinal_position,
    DATA_TYPE AS data_type,
    COLUMN_TYPE AS column_type,
    IS_NULLABLE AS is_nullable,
    COLUMN_DEFAULT AS default_expression,
    EXTRA AS extra,
    GENERATION_EXPRESSION AS generation_expression,
    CHARACTER_SET_NAME AS character_set,
    COLLATION_NAME AS collation_name,
    COLUMN_COMMENT AS comment
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
ORDER BY ORDINAL_POSITION ASC;
"""

# 5. Primary Key Inspection
QUERY_PRIMARY_KEY = """
SELECT
    kcu.COLUMN_NAME AS column_name,
    kcu.ORDINAL_POSITION AS ordinal_position,
    tc.CONSTRAINT_NAME AS constraint_name
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
    ON tc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
   AND tc.TABLE_NAME = kcu.TABLE_NAME
   AND tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
  AND tc.TABLE_SCHEMA = %s
  AND tc.TABLE_NAME = %s
ORDER BY kcu.ORDINAL_POSITION ASC;
"""

# 6. Foreign Key Inspection
QUERY_FOREIGN_KEYS = """
SELECT
    tc.CONSTRAINT_NAME AS constraint_name,
    kcu.COLUMN_NAME AS column_name,
    kcu.REFERENCED_TABLE_SCHEMA AS referenced_schema,
    kcu.REFERENCED_TABLE_NAME AS referenced_table,
    kcu.REFERENCED_COLUMN_NAME AS referenced_column,
    kcu.ORDINAL_POSITION AS ordinal_position,
    rc.UPDATE_RULE AS on_update,
    rc.DELETE_RULE AS on_delete
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
    ON tc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
   AND tc.TABLE_NAME = kcu.TABLE_NAME
   AND tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
    ON tc.CONSTRAINT_SCHEMA = rc.CONSTRAINT_SCHEMA
   AND tc.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
WHERE tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
  AND tc.TABLE_SCHEMA = %s
  AND tc.TABLE_NAME = %s
ORDER BY tc.CONSTRAINT_NAME ASC, kcu.ORDINAL_POSITION ASC;
"""

# 7. Unique Constraint Inspection
QUERY_UNIQUE_CONSTRAINTS = """
SELECT
    tc.CONSTRAINT_NAME AS constraint_name,
    kcu.COLUMN_NAME AS column_name,
    kcu.ORDINAL_POSITION AS ordinal_position
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
    ON tc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
   AND tc.TABLE_NAME = kcu.TABLE_NAME
   AND tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
WHERE tc.CONSTRAINT_TYPE = 'UNIQUE'
  AND tc.TABLE_SCHEMA = %s
  AND tc.TABLE_NAME = %s
ORDER BY tc.CONSTRAINT_NAME ASC, kcu.ORDINAL_POSITION ASC;
"""

# 8. Check Constraint Inspection (MySQL 8.0.16+ and MariaDB 10.2+)
QUERY_CHECK_CONSTRAINTS_MYSQL8 = """
SELECT
    tc.CONSTRAINT_NAME AS constraint_name,
    cc.CHECK_CLAUSE AS check_clause
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
JOIN INFORMATION_SCHEMA.CHECK_CONSTRAINTS cc
    ON tc.CONSTRAINT_SCHEMA = cc.CONSTRAINT_SCHEMA
   AND tc.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
WHERE tc.CONSTRAINT_TYPE = 'CHECK'
  AND tc.TABLE_SCHEMA = %s
  AND tc.TABLE_NAME = %s
ORDER BY tc.CONSTRAINT_NAME ASC;
"""

# Fallback for MariaDB or servers where CHECK_CONSTRAINTS table is structured differently
QUERY_CHECK_CONSTRAINTS_FALLBACK = """
SELECT
    CONSTRAINT_NAME AS constraint_name,
    CHECK_CLAUSE AS check_clause
FROM INFORMATION_SCHEMA.CHECK_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = %s
ORDER BY CONSTRAINT_NAME ASC;
"""

# 9. Index Inspection
# Uses INFORMATION_SCHEMA.STATISTICS
QUERY_INDEXES = """
SELECT
    INDEX_NAME AS index_name,
    NON_UNIQUE AS non_unique,
    SEQ_IN_INDEX AS seq_in_index,
    COLUMN_NAME AS column_name,
    INDEX_TYPE AS index_type,
    SUB_PART AS sub_part,
    COLLATION AS collation,
    COMMENT AS comment
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
ORDER BY INDEX_NAME ASC, SEQ_IN_INDEX ASC;
"""

# MySQL 8.0+ extended index query (with EXPRESSION and IS_VISIBLE)
QUERY_INDEXES_MYSQL8 = """
SELECT
    INDEX_NAME AS index_name,
    NON_UNIQUE AS non_unique,
    SEQ_IN_INDEX AS seq_in_index,
    COLUMN_NAME AS column_name,
    INDEX_TYPE AS index_type,
    SUB_PART AS sub_part,
    COLLATION AS collation,
    EXPRESSION AS expression,
    IS_VISIBLE AS is_visible,
    COMMENT AS comment
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
ORDER BY INDEX_NAME ASC, SEQ_IN_INDEX ASC;
"""

# 10. View Inspection
QUERY_VIEWS = """
SELECT
    TABLE_SCHEMA AS schema_name,
    TABLE_NAME AS view_name,
    VIEW_DEFINITION AS view_definition,
    CHECK_OPTION AS check_option,
    IS_UPDATABLE AS is_updatable,
    DEFINER AS definer,
    SECURITY_TYPE AS security_type
FROM INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = %s
ORDER BY TABLE_NAME ASC;
"""

# 11. Trigger Inspection
QUERY_TRIGGERS = """
SELECT
    TRIGGER_SCHEMA AS schema_name,
    TRIGGER_NAME AS trigger_name,
    EVENT_MANIPULATION AS event_manipulation,
    EVENT_OBJECT_TABLE AS table_name,
    ACTION_TIMING AS action_timing,
    ACTION_STATEMENT AS action_statement,
    DEFINER AS definer
FROM INFORMATION_SCHEMA.TRIGGERS
WHERE TRIGGER_SCHEMA = %s
ORDER BY TRIGGER_NAME ASC;
"""
