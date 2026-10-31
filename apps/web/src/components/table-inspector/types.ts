/**
 * DERA — Table Inspector Domain Types & Presentation Interfaces
 * Phase 7.5: Table Inspector, Advanced Search & Dependency Visualization
 */

import type {
  ColumnDetailItem,
  ConstraintSummaryItem,
  ForeignKeySummaryItem,
  IndexSummaryItem,
  PrimaryKeyItem,
  TableDetailItem,
} from "@/lib/api-client";

/**
 * Universal Object Inspector Interface (Future NoSQL & Multi-Resource Extensibility)
 * Designed for future Firestore, Realtime Database, MongoDB, DynamoDB,
 * and Cloud Database resources without misrepresenting relational structures.
 */
export type InspectorObjectKind =
  | "table"
  | "view"
  | "collection"
  | "document_type"
  | "database_resource";

export interface InspectorObject {
  id: string;
  kind: InspectorObjectKind;
  displayName: string;
  namespace?: string;
  completeness: "complete" | "partial" | "restricted" | "unsupported" | "unknown" | string;
  sourceEngine?: string;
  provenance?: {
    connectorVersion?: string;
    collectionTimestamp?: string;
    sourceMetadataApi?: string;
  };
  metadata?: Record<string, unknown>;
}

export type TableInspectorTab =
  | "columns"
  | "constraints"
  | "indexes"
  | "dependencies"
  | "raw_metadata";

export type ColumnSortField = "ordinal" | "name" | "type" | "nullable";
export type ColumnSortDirection = "asc" | "desc";

export interface TableInspectorState {
  schemaId: string;
  tableId: string;
  activeTab: TableInspectorTab;
  columnSortField: ColumnSortField;
  columnSortDirection: ColumnSortDirection;
  columnFilterQuery: string;
  expandedColumnId: string | null;
}

export interface TableInspectorViewModel {
  table: TableDetailItem;
  schemaId: string;
  connectionId?: string;
  databaseName?: string;
  sourceEngine?: string;
  completeness?: string;
  isSnapshot?: boolean;
  snapshotFingerprint?: string;
  snapshotTimestamp?: string;
}
