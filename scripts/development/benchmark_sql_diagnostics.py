"""Reproducible offline Phase 10.2 benchmark; no customer DB or execution-cost estimates."""

import json
import platform
import statistics
import time
import tracemalloc

from dera.sql_engineering.diagnostics import SqlDiagnosticsEngine

FIXTURES = {
    "small": "SELECT id FROM accounts WHERE id=:id",
    "medium": "SELECT a.id, SUM(b.id) FROM accounts a JOIN users b ON a.id=b.id WHERE a.id>0 GROUP BY a.id ORDER BY a.id",
    "large_multi_cte": "WITH "
    + ", ".join(f"c{i} AS (SELECT id FROM accounts WHERE id>{i})" for i in range(20))
    + " SELECT * FROM c19",
    "deeply_nested": "SELECT * FROM (" * 12 + "SELECT 1" + ") q" * 12,
    "multiple_statements": "; ".join("SELECT id FROM accounts WHERE id=:id" for _ in range(20)),
}


def main():
    engine = SqlDiagnosticsEngine()
    rows = []
    for name, sql in FIXTURES.items():
        engine.analyze(sql, "postgresql")
        latencies = []
        for _ in range(20):
            start = time.perf_counter_ns()
            result = engine.analyze(sql, "postgresql")
            latencies.append((time.perf_counter_ns() - start) / 1_000_000)
        tracemalloc.start()
        engine.analyze(sql, "postgresql")
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        rows.append(
            {
                "fixture": name,
                "utf8_bytes": len(sql.encode()),
                "iterations": 20,
                "median_ms": round(statistics.median(latencies), 3),
                "max_ms": round(max(latencies), 3),
                "tracemalloc_peak_bytes": peak,
                "status": result.analysis_status,
            }
        )
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "engine_version": result.analysis.engine_version,
                "memory_scope": "Separate single-run Python allocation peak; excludes process RSS and native allocations.",
                "results": rows,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
