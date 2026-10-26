import React from "react";
import { Navbar } from "../components/Navbar.js";
import { StatusCard } from "../components/StatusCard.js";

export default function HomePage(): React.ReactElement {
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f9fafb", fontFamily: "system-ui, -apple-system, sans-serif" }}>
      <Navbar />
      <main style={{ maxWidth: "1024px", margin: "0 auto", padding: "3rem 1.5rem" }}>
        <div style={{ textAlign: "center", marginBottom: "3rem" }}>
          <h1 style={{ fontSize: "2.25rem", fontWeight: 800, color: "#111827", marginBottom: "0.75rem", letterSpacing: "-0.03em" }}>
            Understand Every Schema. Engineer Every Change.
          </h1>
          <p style={{ fontSize: "1.125rem", color: "#4b5563", maxWidth: "700px", margin: "0 auto" }}>
            Deterministic database reverse engineering, topological cycle analysis, and migration planning without generative AI or external LLM dependencies.
          </p>
        </div>

        <section style={{ marginBottom: "3rem" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#1f2937", marginBottom: "1rem" }}>
            Platform Foundation Status (Phase 1.2 Baseline)
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
            <StatusCard
              title="Deterministic Core"
              status="Foundation Active"
              description="Canonical schema primitives, topological sorting, and Tarjan's SCC cycle detection implemented."
              isReady={true}
            />
            <StatusCard
              title="SQLite Connector"
              status="Prototype Active"
              description="Read-only metadata extraction via system catalog PRAGMAs with strict query mutation guards."
              isReady={true}
            />
            <StatusCard
              title="PostgreSQL Connector"
              status="In Development"
              description="Full pg_catalog and information_schema introspection scheduled for Phase 5."
              isReady={false}
            />
            <StatusCard
              title="Interactive Studio"
              status="Scaffolding Active"
              description="Next.js workspace established; React Flow schema topology canvas scheduled for Phase 7."
              isReady={false}
            />
          </div>
        </section>

        <section style={{ backgroundColor: "#ffffff", border: "1px solid #e5e7eb", borderRadius: "0.5rem", padding: "1.5rem" }}>
          <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", marginBottom: "0.5rem" }}>
            Deterministic Engineering Guarantees
          </h3>
          <ul style={{ margin: 0, paddingLeft: "1.25rem", color: "#4b5563", lineHeight: 1.6 }}>
            <li>Zero LLMs, zero cloud inference API calls, and zero non-deterministic recommendations.</li>
            <li>Enforced session-level read-only boundaries against all target databases.</li>
            <li>Mathematical graph theory algorithms guaranteeing finite O(V+E) termination.</li>
            <li>Cryptographic SHA-256 schema snapshot hashing for immutable audit trails.</li>
          </ul>
        </section>
      </main>
    </div>
  );
}
