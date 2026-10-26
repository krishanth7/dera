# DERA Package Dependency Graph & Data Flow Architecture

> **Phase:** 1.2 Monorepo Architecture Foundation  
> **Status:** Active Architectural Reference  

---

## 1. Package Dependency Graph

```mermaid
graph TD
    subgraph Frontend Ecosystem
        WEB["apps/web<br/>(Next.js / React Flow)"]
        CONTRACTS["packages/contracts<br/>(TypeScript Interfaces & Schemas)"]
        WEB -->|imports types| CONTRACTS
    end

    subgraph Backend Transport
        API["apps/api<br/>(FastAPI HTTP Gateway)"]
    end

    subgraph Core Domain (Strictly Deterministic)
        CORE["packages/core<br/>(Models, Graph DAG, Diagnostics)"]
        CONNECTORS["packages/connectors<br/>(Read-Only Database Adapters)"]
    end

    subgraph Target Databases (Read-Only)
        SQLITE[("SQLite Database")]
        PG[("PostgreSQL Database")]
        MYSQL[("MySQL Database")]
    end

    API -->|serializes with| CONTRACTS
    API -->|orchestrates| CONNECTORS
    API -->|executes algorithms| CORE
    CONNECTORS -->|constructs| CORE

    CONNECTORS -.->|PRAGMA query_only| SQLITE
    CONNECTORS -.->|SET TRANSACTION READ ONLY| PG
    CONNECTORS -.->|READ ONLY session| MYSQL

    classDef web fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef api fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px;
    classDef core fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef db fill:#fff3e0,stroke:#e65100,stroke-width:2px;

    class WEB,CONTRACTS web;
    class API api;
    class CORE,CONNECTORS core;
    class SQLITE,PG,MYSQL db;
```

---

## 2. End-to-End Introspection Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Engineer / User
    participant Web as apps/web (Studio)
    participant API as apps/api (Gateway)
    participant Conn as packages/connectors
    participant Core as packages/core
    participant DB as Target Database (Read-Only)

    User->>Web: Request Schema Inspection
    Web->>API: GET /api/v1/inspect (config)
    API->>Conn: Instantiate Connector(config)
    Conn->>DB: Connect (Read-Only Session)
    Conn->>DB: Query Catalog (Information Schema / PRAGMA)
    DB-->>Conn: Raw Metadata Rows
    Conn->>Core: Build Canonical Table & Column Primitives
    Core->>Core: Construct SchemaGraph (DAG)
    Core->>Core: Compute Topological Sort & Detect Cycles
    Core->>Core: Run Diagnostic Engine (Missing PK, Unindexed FK)
    Core-->>API: Canonical SchemaSnapshot & Findings
    API-->>Web: JSON Schema Snapshot Contract
    Web-->>User: Render Interactive Visual Topology & Diagnostics
```

---

## 3. Strict Non-AI Boundary Verification

```mermaid
graph LR
    subgraph DERA Deterministic Boundary
        AST[SQLGlot AST Parsing]
        DAG[Tarjan SCC Cycle Detection]
        RULE[Static Rule Diagnostics]
        HASH[Deterministic SHA-256 Hashing]
    end

    subgraph Forbidden External Systems
        LLM[Large Language Models]
        OPENAI[OpenAI API]
        GEMINI[Gemini API]
        CLAUDE[Claude API]
    end

    AST -.->|NO CALLS ALLOWED| LLM
    DAG -.->|NO CALLS ALLOWED| OPENAI
    RULE -.->|NO CALLS ALLOWED| GEMINI
    HASH -.->|NO CALLS ALLOWED| CLAUDE

    style DERA Deterministic Boundary fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px;
    style Forbidden External Systems fill:#ffebee,stroke:#c62828,stroke-width:2px,stroke-dasharray: 5 5;
```
