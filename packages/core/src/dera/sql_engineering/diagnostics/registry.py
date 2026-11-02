"""Closed immutable rule catalog; separate SQL context from Phase 8 schema contexts."""

from collections.abc import Iterable
from dataclasses import dataclass

from dera.diagnostics.enums import DiagnosticSeverity

DIALECTS = ("postgresql", "sqlite", "mysql", "mariadb")


@dataclass(frozen=True)
class Rule:
    rule_id: str
    name: str
    category: str
    description: str
    action: str
    severity: DiagnosticSeverity = DiagnosticSeverity.INFORMATIONAL
    schema_required: bool = False


class RuleRegistry:
    def __init__(self, rules: Iterable[Rule]) -> None:
        rules = tuple(rules)
        if len({r.rule_id for r in rules}) != len(rules):
            raise ValueError("Duplicate SQL rule identifier")
        self.rules = tuple(sorted(rules, key=lambda r: r.rule_id))

    def get(self, rule_id: str) -> Rule:
        return next(r for r in self.rules if r.rule_id == rule_id)


REGISTRY = RuleRegistry(
    (
        Rule(
            "SQL001",
            "SELECT_STAR",
            "projection",
            "Wildcard projection detected.",
            "Consider explicit columns when the result contract is fixed.",
        ),
        Rule(
            "SQL002",
            "MISSING_WHERE_ON_MUTATION",
            "safety",
            "UPDATE or DELETE has no WHERE clause.",
            "Verify the intended affected rows before any external execution.",
            DiagnosticSeverity.HIGH,
        ),
        Rule(
            "SQL003",
            "IMPLICIT_CROSS_JOIN",
            "joins",
            "A join has no explicit condition or join kind.",
            "Review the intended relationship and add an explicit condition when appropriate.",
        ),
        Rule(
            "SQL004",
            "POSSIBLE_CARTESIAN_JOIN",
            "joins",
            "Explicit CROSS JOIN produces row combinations.",
            "Confirm that a Cartesian product is intentional.",
        ),
        Rule(
            "SQL005",
            "NON_SARGABLE_PREDICATE",
            "predicates",
            "A predicate applies a function to a column.",
            "Review expression-index coverage and semantics before changing the predicate.",
        ),
        Rule(
            "SQL006",
            "LEADING_WILDCARD_LIKE",
            "predicates",
            "A LIKE pattern begins with a wildcard.",
            "Review pattern semantics and engine-specific search indexes.",
        ),
        Rule(
            "SQL007",
            "OR_PREDICATE_COMPLEXITY",
            "predicates",
            "At least four OR nodes occur in this statement.",
            "Review predicate grouping and readability; preserve NULL and duplicate semantics.",
        ),
        Rule(
            "SQL008",
            "CORRELATED_SUBQUERY",
            "subqueries",
            "A nested scope refers to an outer-scope column.",
            "Review the correlation with the schema; do not assume a join rewrite is equivalent.",
        ),
        Rule(
            "SQL009",
            "EXCESSIVE_NESTING",
            "complexity",
            "AST depth exceeds 16 levels.",
            "Consider separating logical stages for readability.",
        ),
        Rule(
            "SQL010",
            "EXCESSIVE_JOIN_COUNT",
            "complexity",
            "At least eight joins occur in this statement.",
            "Review join intent, cardinality assumptions and maintainability.",
        ),
        Rule(
            "SQL011",
            "ORDER_BY_WITHOUT_LIMIT",
            "ordering",
            "An ORDER BY has no LIMIT in the same SELECT.",
            "Confirm that ordering the full result is required; no limit is automatically recommended.",
        ),
        Rule(
            "SQL012",
            "DISTINCT_USAGE_REVIEW",
            "aggregation",
            "DISTINCT requests duplicate elimination.",
            "Confirm duplicate semantics and avoid hiding unintended join multiplicity.",
        ),
        Rule(
            "SQL013",
            "GROUP_BY_COMPLEXITY",
            "aggregation",
            "A GROUP BY has more than four expressions.",
            "Review grouping semantics and the intended output grain.",
        ),
        Rule(
            "SQL014",
            "UNSUPPORTED_DIALECT_CONSTRUCT",
            "dialect",
            "The baseline identifies unsupported dialect syntax.",
            "Use syntax supported by the selected grammar and server version.",
        ),
        Rule(
            "SQL015",
            "AMBIGUOUS_COLUMN_REFERENCE",
            "schema",
            "An unqualified column has multiple base-table candidates.",
            "Qualify the column using the intended table alias.",
            schema_required=True,
        ),
        Rule(
            "SQL016",
            "TYPE_COMPATIBILITY_REVIEW",
            "schema",
            "A simple column equality compares different known canonical types.",
            "Review native types and conversion semantics before changing SQL.",
            schema_required=True,
        ),
        Rule(
            "SQL017",
            "UNBOUNDED_RESULT_POTENTIAL",
            "results",
            "A SELECT over a source has neither WHERE nor LIMIT.",
            "Confirm the caller's result-volume contract; aggregates can still return few rows.",
        ),
        Rule(
            "SQL018",
            "NONDETERMINISTIC_ORDERING",
            "ordering",
            "A SELECT has LIMIT without ORDER BY.",
            "If stable paging is required, specify ordering with a verified unique tie-breaker.",
        ),
        Rule(
            "SQL019",
            "EXPENSIVE_SET_OPERATION_PATTERN",
            "set_operations",
            "A set operation requests duplicate elimination.",
            "Use ALL only if retaining duplicates preserves the intended result.",
        ),
        Rule(
            "SQL020",
            "PARSER_OR_ANALYSIS_LIMITATION",
            "analysis",
            "The baseline reports an analysis limitation.",
            "Review the reported capability or input limit before relying on the analysis.",
        ),
        Rule(
            "SQL101",
            "UNKNOWN_TABLE",
            "schema",
            "A base table is absent from a complete snapshot.",
            "Check the selected snapshot, schema qualification and table spelling.",
            schema_required=True,
        ),
        Rule(
            "SQL102",
            "UNKNOWN_COLUMN",
            "schema",
            "A column is absent from resolved base tables in a complete snapshot.",
            "Check aliases, spelling and snapshot freshness.",
            schema_required=True,
        ),
        Rule(
            "SQL103",
            "JOIN_INDEX_COVERAGE_REVIEW",
            "schema",
            "No unconditional leading BTREE index is recorded for a join column.",
            "Review existing index definitions, workload and write cost before proposing any index.",
            schema_required=True,
        ),
        Rule(
            "SQL104",
            "FILTER_INDEX_COVERAGE_REVIEW",
            "schema",
            "No unconditional leading BTREE index is recorded for a filter column.",
            "Review selectivity and existing indexes with a DBA before proposing any index.",
            schema_required=True,
        ),
        Rule(
            "SQL105",
            "FOREIGN_KEY_CONTEXT",
            "schema",
            "A single-column join equality matches a recorded foreign key.",
            "Use the recorded relationship as context; still review join direction and multiplicity.",
            schema_required=True,
        ),
        Rule(
            "SQL106",
            "IDENTIFIER_CASE_REVIEW",
            "schema",
            "Identifier case semantics cannot be established for this reference.",
            "Review server case settings and exact snapshot spelling.",
            schema_required=True,
        ),
    )
)
