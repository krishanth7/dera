# Engine Identifier Semantics & Reserved Words (DERA-MNT-004)

## Dialect-Specific Reserved Keywords

Using SQL keywords as table or column names causes parser failures, query compilation bugs in ORMs, and mandates continuous quoting across application queries.

`DERA-MNT-004` evaluates identifiers against engine-specific reserved word dictionaries:

### PostgreSQL & Supabase
- Core SQL keywords: `select`, `table`, `order`, `group`, `user`, `where`, `check`, etc.
- PostgreSQL-specific keywords: `analyse`, `analyze`, `concurrently`, `freeze`, `ilike`, `lateral`, `tablefunc`, `variadic`, `verbose`.

### MySQL & MariaDB
- MySQL-specific keywords: `accessible`, `asensitive`, `delayed`, `distinctrow`, `dual`, `explain`, `high_priority`, `linear`, `load`, `low_priority`, `optimize`, `purge`, `separator`, `show`, `sql_calc_found_rows`, `starting`, `use`, `xor`, `zerofill`.

### SQLite
- SQLite-specific keywords: `autoincrement`, `glob`, `indexed`, `match`, `plan`, `pragma`, `query`, `regexp`.

## Severity Model
- **Table Name Matches Reserved Keyword**: Classified as `MEDIUM` severity because unquoted table references in `FROM` or `JOIN` clauses immediately fail SQL parsing.
- **Column Name Matches Reserved Keyword**: Classified as `LOW` severity because projection clauses can often alias or quote individual columns.
