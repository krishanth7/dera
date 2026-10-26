import React from "react";

export function Navbar(): React.ReactElement {
  return (
    <header style={{
      borderBottom: "1px solid #e5e7eb",
      padding: "1rem 2rem",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      backgroundColor: "#ffffff",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <span style={{ fontSize: "1.25rem", fontWeight: 700, letterSpacing: "-0.025em", color: "#111827" }}>
          DERA
        </span>
        <span style={{ fontSize: "0.875rem", color: "#6b7280", borderLeft: "1px solid #d1d5db", paddingLeft: "0.75rem" }}>
          Database Engineering & Reverse Analysis
        </span>
      </div>
      <div>
        <span style={{
          fontSize: "0.75rem",
          fontWeight: 600,
          backgroundColor: "#ecfdf5",
          color: "#065f46",
          padding: "0.25rem 0.5rem",
          borderRadius: "0.375rem",
          border: "1px solid #a7f3d0",
        }}>
          ZERO-AI ENGINE
        </span>
      </div>
    </header>
  );
}
