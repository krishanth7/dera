import React from "react";

interface StatusCardProps {
  title: string;
  status: string;
  description: string;
  isReady: boolean;
}

export function StatusCard({ title, status, description, isReady }: StatusCardProps): React.ReactElement {
  return (
    <div style={{
      border: "1px solid #e5e7eb",
      borderRadius: "0.5rem",
      padding: "1.25rem",
      backgroundColor: "#ffffff",
      boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.05)",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.5rem" }}>
        <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#111827", margin: 0 }}>
          {title}
        </h3>
        <span style={{
          fontSize: "0.75rem",
          fontWeight: 600,
          color: isReady ? "#047857" : "#b45309",
          backgroundColor: isReady ? "#d1fae5" : "#fef3c7",
          padding: "0.125rem 0.375rem",
          borderRadius: "0.25rem",
        }}>
          {status}
        </span>
      </div>
      <p style={{ fontSize: "0.875rem", color: "#4b5563", margin: 0, lineHeight: 1.4 }}>
        {description}
      </p>
    </div>
  );
}
