"""Conservative scope-aware checks against verified immutable snapshot payloads."""

from collections import defaultdict

from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

from dera.reverse_engineering.snapshots.models import SchemaSnapshot
from dera.sql_engineering.models import Dialect

SCHEMA_RULES = ("SQL015", "SQL016", "SQL101", "SQL102", "SQL103", "SQL104", "SQL105", "SQL106")


def evaluate(
    tree: exp.Expression, snapshot: SchemaSnapshot | None, dialect: Dialect
) -> tuple[dict[str, tuple[str, ...]], dict[str, str]]:
    facts = defaultdict(list)
    skipped = {}
    if snapshot is None:
        return {}, {r: "No authorized immutable schema snapshot supplied." for r in SCHEMA_RULES}
    if snapshot.completeness != "COMPLETE":
        return {}, {
            r: "Snapshot metadata is incomplete; absence cannot be established."
            for r in SCHEMA_RULES
        }
    tables = snapshot.payload.tables

    def identifier_value(identifier, table=False):
        if not identifier:
            return ""
        name = identifier.name
        if dialect == "sqlite" or (dialect in {"mysql", "mariadb"} and not table):
            return name.casefold()
        if dialect == "postgresql" and not identifier.args.get("quoted"):
            return name.lower()
        return name

    def alias_value(identifier):
        # MySQL-family alias case depends on server configuration: resolve exact spelling only.
        if dialect in {"mysql", "mariadb"}:
            return identifier.name if identifier else ""
        return identifier_value(identifier)

    def native_name(name, table=False):
        return (
            name.casefold()
            if dialect == "sqlite" or (dialect in {"mysql", "mariadb"} and not table)
            else name
        )

    scopes = list(traverse_scope(tree))
    if not scopes:
        return {}, {r: "Schema checks require SELECT scopes." for r in SCHEMA_RULES}
    for scope in scopes:
        sources = {}
        unresolved = False
        for source in scope.sources.values():
            if not isinstance(source, exp.Table):
                unresolved = True
                continue
            if source.catalog:
                unresolved = True
                continue
            name = identifier_value(source.this, table=True)
            namespace = identifier_value(source.args.get("db"), table=True)
            matches = [
                t
                for t in tables
                if native_name(t.name, True) == name
                and (not namespace or native_name(t.namespace, True) == namespace)
            ]
            if len(matches) == 1:
                alias_identifier = (
                    source.args["alias"].this if source.args.get("alias") else source.this
                )
                sources[alias_value(alias_identifier)] = matches[0]
            elif not matches:
                # An exact-case mismatch is not absence when server case rules are unknown.
                case_matches = [
                    t
                    for t in tables
                    if t.name.casefold() == name.casefold()
                    and (not namespace or t.namespace.casefold() == namespace.casefold())
                ]
                if dialect in {"mysql", "mariadb"} and case_matches:
                    facts["SQL106"].append(
                        "Table case differs; lower_case_table_names setting is unavailable."
                    )
                elif any(native_name(v.name, True) == name for v in snapshot.payload.views):
                    unresolved = True
                    continue
                else:
                    facts["SQL101"].append(
                        f"Missing base table: {namespace + '.' if namespace else ''}{name}."
                    )
                unresolved = True
            else:
                unresolved = True
        if unresolved or not sources:
            for rule_id in SCHEMA_RULES:
                if rule_id not in {"SQL101", "SQL106"}:
                    skipped[rule_id] = (
                        "At least one source is derived, missing, ambiguous, cross-catalog or case-indeterminate."
                    )
            continue
        # USING/NATURAL coalesce column names; projection aliases and stars need lineage.
        if any(
            j.args.get("using") or j.args.get("method") == "NATURAL"
            for j in scope.expression.find_all(exp.Join)
        ):
            for r in SCHEMA_RULES:
                if r not in {"SQL101", "SQL106"}:
                    skipped[r] = "USING/NATURAL column coalescence is not resolved."
            continue
        projection_aliases = {
            identifier_value(p.args.get("alias")) for p in scope.expression.expressions if p.alias
        }

        def resolve_column(
            column, sources=sources, projection_aliases=projection_aliases, scope=scope
        ):
            if column.is_star:
                return None
            name = identifier_value(column.this)
            qualifier = alias_value(column.args.get("table"))
            if not qualifier and name in projection_aliases:
                return None
            candidates = [
                (alias, table)
                for alias, table in sources.items()
                if not qualifier or alias == qualifier
            ]
            found = [
                (alias, table, col)
                for alias, table in candidates
                for col in table.columns
                if native_name(col.name) == name
            ]
            if len(found) > 1:
                facts["SQL015"].append(
                    f"Unqualified column {name} has {len(found)} base-table candidates."
                )
            elif not found:
                # Unqualified names may fall through to an outer scope. Do not fabricate absence.
                if not qualifier and scope.parent is not None:
                    skipped["SQL102"] = (
                        "Unqualified nested-scope column may correlate with an outer source."
                    )
                    return None
                # External qualified references may be correlations; do not invent missing columns.
                if not qualifier or qualifier in sources:
                    facts["SQL102"].append(f"Column {name} is absent from resolved base tables.")
            else:
                return found[0]
            return None

        resolved = {}
        for column in scope.columns:
            value = resolve_column(column)
            if value:
                resolved[id(column)] = value
        # Only inspect nodes owned by this scope; nested query columns are handled separately.
        for column in scope.columns:
            value = resolved.get(id(column))
            if not value:
                continue
            _, table, col = value
            ancestor = column.parent
            context = None
            while ancestor and ancestor is not scope.expression:
                if isinstance(ancestor, exp.Select):
                    break
                if isinstance(ancestor, exp.Join):
                    context = "SQL103"
                    break
                if isinstance(ancestor, exp.Where):
                    context = "SQL104"
                    break
                ancestor = ancestor.parent
            if context:
                prefixes = {
                    i.columns[0]
                    for i in table.indexes
                    if i.columns and i.index_type.upper() == "BTREE" and i.predicate is None
                }
                if table.primary_key and table.primary_key.columns:
                    prefixes.add(table.primary_key.columns[0])
                if col.name not in prefixes:
                    facts[context].append(
                        f"{table.namespace}.{table.name}.{col.name}: no recorded unconditional leading BTREE/primary-key coverage; partial and expression indexes may still apply."
                    )
            parent = column.parent
            if (
                not isinstance(parent, exp.EQ)
                or parent.this is not column
                or not isinstance(parent.expression, exp.Column)
            ):
                continue
            other = resolved.get(id(parent.expression))
            if not other:
                continue
            _, other_table, other_col = other
            if col.canonical_type != other_col.canonical_type and "UNKNOWN" not in {
                str(col.canonical_type),
                str(other_col.canonical_type),
            }:
                facts["SQL016"].append(
                    f"Equality compares {col.canonical_type} and {other_col.canonical_type}; native conversion behavior not inferred."
                )
            if context == "SQL103":
                for left, left_col, right, right_col in (
                    (table, col, other_table, other_col),
                    (other_table, other_col, table, col),
                ):
                    for fk in left.foreign_keys:
                        if (
                            fk.source_columns == (left_col.name,)
                            and fk.target_namespace == right.namespace
                            and fk.target_table == right.name
                            and fk.target_columns == (right_col.name,)
                        ):
                            facts["SQL105"].append(
                                f"Recorded FK {fk.name}: {left.namespace}.{left.name}.{left_col.name} -> {right.namespace}.{right.name}.{right_col.name}."
                            )
    return {k: tuple(sorted(set(v))) for k, v in facts.items()}, skipped
