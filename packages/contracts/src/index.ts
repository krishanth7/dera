/**
 * DERA — Database Engineering & Reverse Analysis
 * Shared Canonical Schema Contracts (TypeScript)
 *
 * Deterministic database models and static rule interfaces.
 * Copyright (c) 2026 Bunga Krishanth. All rights reserved.
 * Licensed under the MIT License.
 */

export interface DatabaseColumn {
  name: string;
  data_type: string;
  nullable: boolean;
  default_value?: string | null;
  is_primary_key: boolean;
  comment?: string | null;
}

export interface PrimaryKeyConstraint {
  name: string;
  columns: string[];
}

export interface ForeignKeyConstraint {
  name: string;
  constrained_columns: string[];
  referenced_table: string;
  referenced_columns: string[];
  on_delete: "NO ACTION" | "RESTRICT" | "CASCADE" | "SET NULL" | "SET DEFAULT";
  on_update: "NO ACTION" | "RESTRICT" | "CASCADE" | "SET NULL" | "SET DEFAULT";
}

export interface TableIndex {
  name: string;
  columns: string[];
  is_unique: boolean;
  method: string;
}

export interface DatabaseTable {
  schema: string;
  name: string;
  columns: DatabaseColumn[];
  primary_key?: PrimaryKeyConstraint | null;
  foreign_keys: ForeignKeyConstraint[];
  indexes: TableIndex[];
  comment?: string | null;
}

export interface SchemaSnapshot {
  version: string;
  dialect: "postgresql" | "mysql" | "sqlite" | "sqlserver";
  extracted_at: string;
  tables: Record<string, DatabaseTable>;
  metadata: Record<string, unknown>;
}

export interface DiagnosticFinding {
  rule_id: string;
  severity: "info" | "warning" | "critical";
  table: string;
  message: string;
  remediation?: string;
}

export interface TableDependencyGraph {
  nodes: string[];
  edges: Array<{
    source: string;
    target: string;
    foreign_key: string;
  }>;
  topological_order: string[];
  has_cycle: boolean;
}
