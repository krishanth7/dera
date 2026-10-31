/**
 * DERA — Database Engineering & Reverse Analysis
 * Web Visualizer & Canvas Entrypoint
 *
 * Deterministic schema topology visualizer and diagnostic inspector.
 * Copyright (c) 2026 Krishanth. All rights reserved.
 * Licensed under the MIT License.
 */

import type {
  SchemaSnapshot,
  TableDependencyGraph,
  DiagnosticFinding,
} from "@dera/contracts";

export interface CanvasViewport {
  zoom: number;
  panX: number;
  panY: number;
}

export class DeraSchemaCanvas {
  private snapshot: SchemaSnapshot | null = null;
  private graph: TableDependencyGraph | null = null;
  private findings: DiagnosticFinding[] = [];
  private viewport: CanvasViewport = { zoom: 1.0, panX: 0, panY: 0 };

  constructor(snapshot?: SchemaSnapshot) {
    if (snapshot) {
      this.loadSnapshot(snapshot);
    }
  }

  public loadSnapshot(snapshot: SchemaSnapshot): void {
    this.snapshot = snapshot;
  }

  public getSnapshot(): SchemaSnapshot | null {
    return this.snapshot;
  }

  public setFindings(findings: DiagnosticFinding[]): void {
    this.findings = [...findings];
  }

  public getFindings(): DiagnosticFinding[] {
    return this.findings;
  }

  public getViewport(): CanvasViewport {
    return { ...this.viewport };
  }

  public setViewport(viewport: Partial<CanvasViewport>): void {
    this.viewport = { ...this.viewport, ...viewport };
  }
}

export * from "./components/diagnostics";
export * from "./lib/diagnostics";
