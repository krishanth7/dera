"""DERA PostgreSQL Connector — System Catalog Introspection Queries.

Defines safe, strictly parameterized read-only SQL queries targeting pg_catalog.
Never queries customer data tables, never executes stored procedures, and produces
deterministic row orderings across all PostgreSQL versions (14–18).
"""

QUERY_IDENTITY = """
SELECT
    version() AS full_version,
    current_setting('server_version_num')::integer AS version_num,
    current_database() AS current_database,
    current_user AS current_user;
"""

QUERY_SCHEMAS = """
SELECT
    n.nspname AS schema_name,
    d.description AS comment
FROM pg_catalog.pg_namespace n
LEFT JOIN pg_catalog.pg_description d
    ON d.objoid = n.oid AND d.classoid = 'pg_namespace'::regclass
WHERE n.nspname NOT LIKE 'pg_toast%'
  AND n.nspname NOT LIKE 'pg_temp%'
ORDER BY n.nspname ASC;
"""

QUERY_TABLES = """
SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    CASE c.relkind
        WHEN 'r' THEN 'TABLE'
        WHEN 'p' THEN 'PARTITIONED TABLE'
        WHEN 'f' THEN 'FOREIGN TABLE'
        ELSE 'TABLE'
    END AS object_type,
    d.description AS comment,
    c.relpersistence = 'u' AS is_unlogged,
    c.relkind = 'p' AS is_partitioned
FROM pg_catalog.pg_class c
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_catalog.pg_description d
    ON d.objoid = c.oid AND d.objsubid = 0 AND d.classoid = 'pg_class'::regclass
WHERE c.relkind IN ('r', 'p', 'f')
  AND n.nspname NOT LIKE 'pg_toast%'
  AND n.nspname NOT LIKE 'pg_temp%'
  AND ($1::text IS NULL OR n.nspname = $1::text)
ORDER BY n.nspname ASC, c.relname ASC;
"""

QUERY_COLUMNS = """
SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    a.attname AS column_name,
    a.attnum::integer AS ordinal_position,
    format_type(a.atttypid, a.atttypmod) AS data_type,
    NOT a.attnotnull AS is_nullable,
    pg_get_expr(def.adbin, def.adrelid) AS default_expression,
    (a.attidentity != '') AS is_identity,
    (a.attgenerated != '') AS is_generated,
    CASE WHEN a.attgenerated != '' THEN pg_get_expr(def.adbin, def.adrelid) ELSE NULL END AS generation_expression,
    d.description AS comment,
    coll.collname AS collation_name
FROM pg_catalog.pg_attribute a
JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_catalog.pg_attrdef def ON def.adrelid = a.attrelid AND def.adnum = a.attnum
LEFT JOIN pg_catalog.pg_description d
    ON d.objoid = c.oid AND d.objsubid = a.attnum AND d.classoid = 'pg_class'::regclass
LEFT JOIN pg_catalog.pg_collation coll ON coll.oid = a.attcollation AND a.attcollation != 0
WHERE a.attnum > 0
  AND NOT a.attisdropped
  AND ($1::text IS NULL OR n.nspname = $1::text)
  AND c.relname = $2::text
ORDER BY a.attnum ASC;
"""

QUERY_PRIMARY_KEY = """
SELECT
    con.conname AS constraint_name,
    n.nspname AS schema_name,
    c.relname AS table_name,
    ARRAY(
        SELECT a.attname
        FROM unnest(con.conkey) WITH ORDINALITY AS u(attnum, ord)
        JOIN pg_catalog.pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = u.attnum
        ORDER BY u.ord
    ) AS column_names
FROM pg_catalog.pg_constraint con
JOIN pg_catalog.pg_class c ON c.oid = con.conrelid
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE con.contype = 'p'
  AND ($1::text IS NULL OR n.nspname = $1::text)
  AND c.relname = $2::text
LIMIT 1;
"""

QUERY_FOREIGN_KEYS = """
SELECT
    con.conname AS constraint_name,
    n.nspname AS schema_name,
    c.relname AS table_name,
    ARRAY(
        SELECT a.attname
        FROM unnest(con.conkey) WITH ORDINALITY AS u(attnum, ord)
        JOIN pg_catalog.pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = u.attnum
        ORDER BY u.ord
    ) AS column_names,
    rn.nspname AS referenced_schema,
    rc.relname AS referenced_table,
    ARRAY(
        SELECT ra.attname
        FROM unnest(con.confkey) WITH ORDINALITY AS ru(attnum, ord)
        JOIN pg_catalog.pg_attribute ra ON ra.attrelid = con.confrelid AND ra.attnum = ru.attnum
        ORDER BY ru.ord
    ) AS referenced_columns,
    CASE con.confupdtype
        WHEN 'a' THEN 'NO ACTION'
        WHEN 'r' THEN 'RESTRICT'
        WHEN 'c' THEN 'CASCADE'
        WHEN 'n' THEN 'SET NULL'
        WHEN 'd' THEN 'SET DEFAULT'
        ELSE 'NO ACTION'
    END AS on_update,
    CASE con.confdeltype
        WHEN 'a' THEN 'NO ACTION'
        WHEN 'r' THEN 'RESTRICT'
        WHEN 'c' THEN 'CASCADE'
        WHEN 'n' THEN 'SET NULL'
        WHEN 'd' THEN 'SET DEFAULT'
        ELSE 'NO ACTION'
    END AS on_delete
FROM pg_catalog.pg_constraint con
JOIN pg_catalog.pg_class c ON c.oid = con.conrelid
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
JOIN pg_catalog.pg_class rc ON rc.oid = con.confrelid
JOIN pg_catalog.pg_namespace rn ON rn.oid = rc.relnamespace
WHERE con.contype = 'f'
  AND ($1::text IS NULL OR n.nspname = $1::text)
  AND c.relname = $2::text
ORDER BY con.conname ASC;
"""

QUERY_UNIQUE_CONSTRAINTS = """
SELECT
    con.conname AS constraint_name,
    n.nspname AS schema_name,
    c.relname AS table_name,
    ARRAY(
        SELECT a.attname
        FROM unnest(con.conkey) WITH ORDINALITY AS u(attnum, ord)
        JOIN pg_catalog.pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = u.attnum
        ORDER BY u.ord
    ) AS column_names
FROM pg_catalog.pg_constraint con
JOIN pg_catalog.pg_class c ON c.oid = con.conrelid
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE con.contype = 'u'
  AND ($1::text IS NULL OR n.nspname = $1::text)
  AND c.relname = $2::text
ORDER BY con.conname ASC;
"""

QUERY_CHECK_CONSTRAINTS = """
SELECT
    con.conname AS constraint_name,
    n.nspname AS schema_name,
    c.relname AS table_name,
    pg_get_constraintdef(con.oid, true) AS check_clause
FROM pg_catalog.pg_constraint con
JOIN pg_catalog.pg_class c ON c.oid = con.conrelid
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE con.contype = 'c'
  AND ($1::text IS NULL OR n.nspname = $1::text)
  AND c.relname = $2::text
ORDER BY con.conname ASC;
"""

QUERY_INDEXES = """
SELECT
    ci.relname AS index_name,
    n.nspname AS schema_name,
    ct.relname AS table_name,
    i.indisunique AS is_unique,
    i.indisprimary AS is_primary,
    am.amname AS index_type,
    pg_get_expr(i.indpred, i.indrelid) AS predicate,
    ARRAY(
        SELECT pg_get_indexdef(i.indexrelid, k + 1, true)
        FROM generate_series(0, i.indnatts - 1) AS k
    ) AS column_names
FROM pg_catalog.pg_index i
JOIN pg_catalog.pg_class ci ON ci.oid = i.indexrelid
JOIN pg_catalog.pg_class ct ON ct.oid = i.indrelid
JOIN pg_catalog.pg_namespace n ON n.oid = ct.relnamespace
JOIN pg_catalog.pg_am am ON am.oid = ci.relam
WHERE ($1::text IS NULL OR n.nspname = $1::text)
  AND ct.relname = $2::text
ORDER BY ci.relname ASC;
"""

QUERY_VIEWS = """
SELECT
    n.nspname AS schema_name,
    c.relname AS view_name,
    (c.relkind = 'm') AS is_materialized,
    pg_get_viewdef(c.oid, true) AS view_definition,
    d.description AS comment
FROM pg_catalog.pg_class c
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_catalog.pg_description d
    ON d.objoid = c.oid AND d.objsubid = 0 AND d.classoid = 'pg_class'::regclass
WHERE c.relkind IN ('v', 'm')
  AND n.nspname NOT LIKE 'pg_toast%'
  AND n.nspname NOT LIKE 'pg_temp%'
  AND ($1::text IS NULL OR n.nspname = $1::text)
ORDER BY n.nspname ASC, c.relname ASC;
"""

QUERY_SEQUENCES = """
SELECT
    n.nspname AS schema_name,
    c.relname AS sequence_name,
    format_type(s.seqtypid, null) AS data_type,
    s.seqstart::bigint AS start_value,
    s.seqmin::bigint AS minimum_value,
    s.seqmax::bigint AS maximum_value,
    s.seqincrement::bigint AS increment,
    s.seqcycle AS is_cycling,
    d.description AS comment
FROM pg_catalog.pg_sequence s
JOIN pg_catalog.pg_class c ON c.oid = s.seqrelid
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_catalog.pg_description d
    ON d.objoid = c.oid AND d.objsubid = 0 AND d.classoid = 'pg_class'::regclass
WHERE ($1::text IS NULL OR n.nspname = $1::text)
ORDER BY n.nspname ASC, c.relname ASC;
"""

QUERY_PARTITIONS = """
SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    CASE pt.partstrat
        WHEN 'r' THEN 'RANGE'
        WHEN 'l' THEN 'LIST'
        WHEN 'h' THEN 'HASH'
        ELSE 'UNKNOWN'
    END AS partition_strategy,
    ARRAY(
        SELECT a.attname
        FROM unnest(pt.partattrs) WITH ORDINALITY AS u(attnum, ord)
        JOIN pg_catalog.pg_attribute a ON a.attrelid = pt.partrelid AND a.attnum = u.attnum
        ORDER BY u.ord
    ) AS partition_key_columns,
    pg_get_expr(c.relpartbound, c.oid) AS partition_bound_expression,
    pn.nspname AS parent_schema,
    pc.relname AS parent_table
FROM pg_catalog.pg_class c
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_catalog.pg_partitioned_table pt ON pt.partrelid = c.oid
LEFT JOIN pg_catalog.pg_inherits inh ON inh.inhrelid = c.oid
LEFT JOIN pg_catalog.pg_class pc ON pc.oid = inh.inhparent
LEFT JOIN pg_catalog.pg_namespace pn ON pn.oid = pc.relnamespace
WHERE (c.relkind = 'p' OR c.relispartition)
  AND ($1::text IS NULL OR n.nspname = $1::text)
  AND ($2::text IS NULL OR c.relname = $2::text)
ORDER BY n.nspname ASC, c.relname ASC;
"""
