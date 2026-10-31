/**
 * DERA — Dependency Explorer Types & Contracts
 * Phase 7.5: Table Inspector, Advanced Search & Dependency Visualization
 */

import type {
  DependencyAnalysisResponse,
  CycleReportResponse,
  RelationshipGraphResponse,
} from "@/lib/api-client";

export type DependencyDirection = "both" | "outgoing" | "incoming";
export type DependencyDepth = 1 | 2 | 3 | "transitive";

export type DependencyExplorerView =
  | "summary"
  | "reachability"
  | "cycles"
  | "ordering"
  | "accessible_table";

export interface DependencyExplorerViewModel {
  schemaId: string;
  databaseName?: string;
  sourceEngine?: string;
  completeness?: string;
  analysis: DependencyAnalysisResponse;
  cycles: CycleReportResponse;
  relationships: RelationshipGraphResponse;
  initialTableId?: string;
}

export interface ReachabilityNode {
  tableId: string;
  tableName: string;
  namespace: string;
  depth: number;
  direction: "upstream" | "downstream";
  viaConstraint?: string;
}
