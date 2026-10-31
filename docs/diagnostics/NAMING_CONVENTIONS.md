# Identifier Naming Conventions & Profiles (DERA-MNT-003)

## Overview

Inconsistent identifier casing and naming styles across database tables and columns increase developer cognitive load, complicate Object-Relational Mapping (ORM) schema generation, and lead to escaping bugs in multi-dialect queries.

Rule `DERA-MNT-003` detects deviations from a configured naming convention profile.

## Supported Naming Profiles

| Profile Name | Regular Expression Pattern | Example Valid Identifiers |
| :--- | :--- | :--- |
| `snake_case` (Default) | `^[a-z][a-z0-9]*(_[a-z0-9]+)*$` | `user_id`, `created_at`, `order_items` |
| `camelCase` | `^[a-z][a-zA-Z0-9]*$` | `userId`, `createdAt`, `orderItems` |
| `PascalCase` | `^[A-Z][a-zA-Z0-9]*$` | `UserId`, `CreatedAt`, `OrderItems` |
| `kebab-case` | `^[a-z][a-z0-9]*(-[a-z0-9]+)*$` | `user-id`, `created-at`, `order-items` |
| `UPPER_SNAKE_CASE` | `^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$` | `USER_ID`, `CREATED_AT`, `ORDER_ITEMS` |

## Identifier Normalization & Quoting

Prior to regex evaluation, identifiers are normalized:
1. Surrounding identifier quotes (`"identifier"`, `` `identifier` ``, `[identifier]`) are stripped.
2. Engine-specific case folding is respected (PostgreSQL folds unquoted identifiers to lowercase, MySQL on Windows is case-insensitive by default).

## Severity Policy

Naming convention deviations are classified with `INFORMATIONAL` severity. Style deviations are not treated as data integrity defects.
