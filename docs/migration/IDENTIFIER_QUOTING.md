# Phase 9.4 Identifier Quoting & SQL Safety

## Dialect Quoting Rules
Safe identifier quoting prevents SQL injection vulnerabilities and ensures safe interpolation of reserved words, case-sensitive names, and unicode identifiers.

| Dialect | Quoting Character | Escaping Rule | Example |
|---|---|---|---|
| **PostgreSQL** | Double quote (`"`) | Double embedded quote (`""`) | `"public"."users"` |
| **Supabase** | Double quote (`"`) | Double embedded quote (`""`) | `"public"."users"` |
| **SQLite** | Double quote (`"`) | Double embedded quote (`""`) | `"posts"` |
| **MySQL** | Backtick (``` ` ```) | Double embedded backtick (`` `` ``) | `` `shop`.`orders` `` |
| **MariaDB** | Backtick (``` ` ```) | Double embedded backtick (`` `` ``) | `` `shop`.`orders` `` |

## Injection Protections
1. **Null Byte Elimination:** Any identifier containing `\x00` is rejected immediately with a `ValueError`.
2. **Literal Token Escaping:** Semicolons, comments (`--`, `/*`), and quotes inside table or column names are neutralized by outer dialect quotation and inner quote doubling.
3. **Traceability:** Every statement generated is assigned an immutable SHA-256 statement fingerprint.
