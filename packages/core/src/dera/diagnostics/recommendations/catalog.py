"""DERA Diagnostics — Recommendation Catalog.

Contains structured, deterministic engineering recommendation specifications
covering indexes, constraints, relationships, dependencies, and maintainability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RECOMMENDATION_CATALOG_VERSION = "1.0.0"


@dataclass(frozen=True)
class RecommendationEntry:
    """Catalog specification for a deterministic engineering recommendation."""

    recommendation_id: str
    applicable_rule_ids: tuple[str, ...]
    title: str
    description: str
    preconditions: tuple[str, ...]
    suggested_action: str
    risk_considerations: str
    verification_steps: tuple[str, ...]
    limitations: str
    version: str = "1.0.0"

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "applicable_rule_ids": list(self.applicable_rule_ids),
            "title": self.title,
            "description": self.description,
            "preconditions": list(self.preconditions),
            "suggested_action": self.suggested_action,
            "risk_considerations": self.risk_considerations,
            "verification_steps": list(self.verification_steps),
            "limitations": self.limitations,
            "version": self.version,
        }


# Comprehensive, advisory-only recommendation catalog for Phase 8.1-8.4 rules
RECOMMENDATION_CATALOG: tuple[RecommendationEntry, ...] = (
    # Foundational & Schema Integrity
    RecommendationEntry(
        recommendation_id="REC-SCHEMA-001",
        applicable_rule_ids=("DERA-SCHEMA-001",),
        title="Resolve Canonical Identity Collision",
        description="Two or more schema entities resolve to identical case-folded or unquoted canonical identifiers.",
        preconditions=("Target entities exist in the same namespace or database catalog.",),
        suggested_action="Review and rename colliding schema entities to maintain distinct identifier boundaries across all supported database engines.",
        risk_considerations="Renaming existing tables or columns requires updating application queries, ORM models, and views.",
        verification_steps=(
            "Verify entity names in source catalog.",
            "Confirm no downstream application queries reference the duplicate name.",
        ),
        limitations="Static analysis cannot determine which colliding entity was created first.",
    ),
    RecommendationEntry(
        recommendation_id="REC-SCHEMA-002",
        applicable_rule_ids=("DERA-SCHEMA-002",),
        title="Populate Missing Structural Metadata",
        description="Table or view entity definition lacks column specifications or type information.",
        preconditions=("Connector returned incomplete catalog metadata during inspection.",),
        suggested_action="Verify database user permissions to ensure full read access to information schema and system catalogs.",
        risk_considerations="Insufficient metadata inspection permissions may mask underlying structural defects.",
        verification_steps=(
            "Inspect database user GRANT permissions.",
            "Re-run extraction with elevated metadata inspection privileges.",
        ),
        limitations="Does not mutate permissions or execute database commands.",
    ),
    # Index Recommendations
    RecommendationEntry(
        recommendation_id="REC-IDX-001",
        applicable_rule_ids=("DERA-IDX-001",),
        title="Review Duplicate Indexes for Consolidation",
        description="Multiple indexes declare identical column sequences and options.",
        preconditions=("Duplicate index definitions verified in catalog metadata.",),
        suggested_action="Evaluate whether duplicate indexes can be consolidated. Retain primary or constraint-backing index and consider removing redundant secondary copies.",
        risk_considerations="Do not drop indexes without verifying optimizer query plans and active workload statistics.",
        verification_steps=(
            "Examine query execution plans to verify index usage.",
            "Verify index is not explicitly hinted by application queries.",
        ),
        limitations="DERA does not execute index drops or predict runtime query latency without production metrics.",
    ),
    RecommendationEntry(
        recommendation_id="REC-IDX-002",
        applicable_rule_ids=("DERA-IDX-002",),
        title="Review Redundant Prefix Indexes",
        description="An index is a strict left-prefix of another index on the same table.",
        preconditions=("Compound index with identical leading columns exists.",),
        suggested_action="Assess whether the shorter prefix index can be covered by the composite index.",
        risk_considerations="Removing prefix indexes may affect queries requiring smaller index footprints in memory.",
        verification_steps=(
            "Confirm composite index satisfies queries filtering on the prefix column.",
            "Verify table index size and buffer cache footprint.",
        ),
        limitations="Does not automatically drop indexes.",
    ),
    RecommendationEntry(
        recommendation_id="REC-IDX-003",
        applicable_rule_ids=("DERA-IDX-003",),
        title="Evaluate Foreign Key Index Coverage",
        description="Foreign key constraint lacks supporting leading index on constrained columns.",
        preconditions=("Table has active foreign key referencing parent entity.",),
        suggested_action="Examine join and delete workloads against parent table to evaluate whether creating an index on foreign key columns will prevent table locks or full scans.",
        risk_considerations="Adding indexes increases write amplification during INSERT and UPDATE operations.",
        verification_steps=(
            "Monitor parent table DELETE and UPDATE frequencies.",
            "Test query performance with an index on constrained columns.",
        ),
        limitations="Workload volume and write overhead dictate whether index is warranted.",
    ),
    RecommendationEntry(
        recommendation_id="REC-IDX-004",
        applicable_rule_ids=("DERA-IDX-004",),
        title="Repair Index Referencing Non-Existent Column",
        description="Index metadata references a column name that does not exist on the target table.",
        preconditions=("Orphaned index definition detected in catalog.",),
        suggested_action="Recreate or rebuild index with existing columns, or restore missing column.",
        risk_considerations="Invalid indexes may prevent table DDL operations or cause query failures.",
        verification_steps=(
            "Inspect table column definitions.",
            "Verify index validity in system catalog.",
        ),
        limitations="Static analysis verifies column presence only.",
    ),
    # Constraint Recommendations
    RecommendationEntry(
        recommendation_id="REC-CON-001",
        applicable_rule_ids=("DERA-CON-001",),
        title="Define Explicit Primary Key Constraint",
        description="Table lacks an explicit primary key constraint.",
        preconditions=("Table contains rows requiring unique row identification.",),
        suggested_action="Review table data model and designate a primary key column or composite key to ensure deterministic row identification and replication safety.",
        risk_considerations="Adding a primary key requires ensuring existing column values are non-null and unique.",
        verification_steps=(
            "Verify uniqueness of candidate key columns.",
            "Ensure candidate columns are NOT NULL.",
        ),
        limitations="Static analysis does not inspect row data to find unique candidates.",
    ),
    RecommendationEntry(
        recommendation_id="REC-CON-002",
        applicable_rule_ids=("DERA-CON-002",),
        title="Resolve Unresolved Foreign Key Target",
        description="Foreign key constraint references a table that does not exist in schema metadata.",
        preconditions=("Constraint references missing or un-extracted table.",),
        suggested_action="Verify whether referenced table was excluded during extraction or dropped from the database catalog.",
        risk_considerations="Dangling foreign keys cause relational integrity violations.",
        verification_steps=(
            "Confirm existence of referenced table in database.",
            "Check namespace qualification in foreign key definition.",
        ),
        limitations="Cannot determine if target exists in an un-extracted external database.",
    ),
    RecommendationEntry(
        recommendation_id="REC-CON-003",
        applicable_rule_ids=("DERA-CON-003",),
        title="Align Foreign Key Columns with Unique Target",
        description="Foreign key references columns that do not form a primary or unique key on the target table.",
        preconditions=("Referenced table exists but lacks matching unique constraint.",),
        suggested_action="Add unique constraint to target columns or adjust foreign key to reference the primary key.",
        risk_considerations="Relational databases require target columns of foreign keys to be uniquely constrained.",
        verification_steps=(
            "Inspect target table primary key and unique constraints.",
            "Verify cardinality of referenced data.",
        ),
        limitations="Advisory guidance only.",
    ),
    # Relationship & Dependency Recommendations
    RecommendationEntry(
        recommendation_id="REC-REL-001",
        applicable_rule_ids=("DERA-REL-001", "DERA-REL-002", "DERA-REL-003"),
        title="Validate Foreign Key Graph Consistency",
        description="Foreign key relationships contain graph integrity discrepancies or composite mapping mismatches.",
        preconditions=("Relationship graph constructed from schema constraints.",),
        suggested_action="Audit foreign key column mappings and ensure column count and types match target definitions exactly.",
        risk_considerations="Inconsistent mappings lead to runtime constraint enforcement failures.",
        verification_steps=(
            "Check column data types and orders in source and target tables.",
            "Run schema validation scripts.",
        ),
        limitations="Directional graph analysis is static.",
    ),
    RecommendationEntry(
        recommendation_id="REC-DEP-001",
        applicable_rule_ids=("DERA-DEP-001",),
        title="Break Circular Foreign Key Dependencies",
        description="A cycle of foreign key references exists between tables.",
        preconditions=("Cycle detected via Tarjan's strongly connected components algorithm.",),
        suggested_action="Review circular relationship group. Consider introducing an intermediate junction entity or making one foreign key nullable/deferred.",
        risk_considerations="Circular dependencies complicate data insertion, deletion, truncation, and migration order.",
        verification_steps=(
            "Trace dependency loop sequence.",
            "Test data loading order and transactional deferral behavior.",
        ),
        limitations="Does not auto-refactor schema relationships.",
    ),
    RecommendationEntry(
        recommendation_id="REC-DEP-002",
        applicable_rule_ids=("DERA-DEP-002", "DERA-DEP-003", "DERA-DEP-004"),
        title="Manage High Dependency Concentration and Depth",
        description="Entity participates in an excessively deep dependency chain or exhibits high fan-in/fan-out.",
        preconditions=("Dependency depth or concentration exceeds configured threshold.",),
        suggested_action="Review domain architecture to modularize tightly coupled entities into separate bounded contexts.",
        risk_considerations="Highly central tables present single points of failure during schema migrations.",
        verification_steps=(
            "Analyze impact blast radius for proposed column changes.",
            "Audit application touchpoints for the central table.",
        ),
        limitations="Architectural decisions depend on domain boundary requirements.",
    ),
    # Maintainability Recommendations
    RecommendationEntry(
        recommendation_id="REC-MNT-001",
        applicable_rule_ids=("DERA-MNT-001",),
        title="Review Unusually Wide Tables",
        description="Table declares a large number of columns exceeding maintainability thresholds.",
        preconditions=("Column count exceeds configured threshold.",),
        suggested_action="Evaluate whether wide tables contain mixed concerns or one-to-one extension attributes that can be partitioned into vertical domain entities.",
        risk_considerations="Splitting tables requires updating application queries and joining rows.",
        verification_steps=(
            "Categorize columns by access frequency and mutability.",
            "Evaluate row size against database page size limits.",
        ),
        limitations="Wide tables may be intentionally designed for analytical reporting or wide denormalization.",
    ),
    RecommendationEntry(
        recommendation_id="REC-MNT-002",
        applicable_rule_ids=("DERA-MNT-002",),
        title="Review Excessive Column Nullability",
        description="A high proportion of table columns are nullable.",
        preconditions=("Nullability ratio exceeds configured threshold.",),
        suggested_action="Evaluate whether optional attributes belong in a separate subtype table or JSONB/document structure.",
        risk_considerations="Changing column nullability requires data cleanup of existing null values.",
        verification_steps=(
            "Query tables for actual null value density in production.",
            "Audit business requirements for column presence.",
        ),
        limitations="Static analysis inspects schema definition, not table row data density.",
    ),
    RecommendationEntry(
        recommendation_id="REC-MNT-003",
        applicable_rule_ids=("DERA-MNT-003", "DERA-MNT-004"),
        title="Standardize Naming Conventions and Avoid Reserved Keywords",
        description="Object names deviate from standard casing styles or collide with SQL reserved words.",
        preconditions=(
            "Name violates configured casing pattern or matches reserved word dictionary.",
        ),
        suggested_action="Adopt consistent snake_case naming and avoid SQL reserved words to prevent mandatory quoting in queries.",
        risk_considerations="Renaming existing tables or columns requires updating application queries, ORM models, and views.",
        verification_steps=(
            "Check naming convention guidelines.",
            "Verify all queries handle identifier quoting if name is not changed.",
        ),
        limitations="Naming conventions are team-specific engineering preferences.",
    ),
    RecommendationEntry(
        recommendation_id="REC-MNT-008",
        applicable_rule_ids=("DERA-MNT-008",),
        title="Manage LOB Column Concentration",
        description="Table contains multiple Large Object (LOB) columns (TEXT, BLOB, BYTEA).",
        preconditions=("Multiple LOB columns defined on a single table.",),
        suggested_action="Consider storing large binary assets in object storage (e.g. S3, GCS) and storing URIs in database columns, or segregating LOBs to secondary tables.",
        risk_considerations="Excessive inline LOB data degrades buffer pool efficiency and table scan performance.",
        verification_steps=(
            "Measure average row size and TOAST/overflow page usage.",
            "Assess read/write frequency of LOB attributes.",
        ),
        limitations="Database storage engines vary in how off-page LOB storage is handled.",
    ),
)


def get_recommendation_for_rule(rule_id: str) -> RecommendationEntry | None:
    """Finds the catalog recommendation entry matching the given rule_id."""
    for entry in RECOMMENDATION_CATALOG:
        if rule_id in entry.applicable_rule_ids:
            return entry
    return None
