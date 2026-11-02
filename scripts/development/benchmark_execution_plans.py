"""Reproducible offline parser/normalizer/rule/serializer timings and peak traced allocations."""

import json
import platform
import statistics
import time
import tracemalloc

from dera.sql_engineering.execution_plans import analyze_plan
from dera.sql_engineering.execution_plans.analysis import analyze_nodes
from dera.sql_engineering.execution_plans.normalizer import normalize
from dera.sql_engineering.execution_plans.parser import canonical, decode


def fixture(count, padding=0):
    return json.dumps(
        {
            "Plan": {
                "Node Type": "Append",
                "Total Cost": 100,
                "Plans": [
                    {
                        "Node Type": "Seq Scan",
                        "Plan Rows": 10000,
                        "Total Cost": 10,
                        "Relation Name": f"table_{i}",
                        "Filter": "x" * padding,
                    }
                    for i in range(count - 1)
                ],
            }
        }
    )


def main():
    deep = {"Node Type": "Result"}
    for _ in range(24):
        deep = {"Node Type": "Result", "Plans": [deep]}
    fixtures = {
        "10_nodes": fixture(10),
        "100_nodes": fixture(100),
        "1000_nodes": fixture(1000),
        "deep_25": json.dumps({"Plan": deep}),
        "large_import": fixture(1000, 600),
    }
    results = []
    for name, text in fixtures.items():
        samples = {
            key: []
            for key in ("decode_ms", "normalize_ms", "diagnostics_ms", "serialize_ms", "total_ms")
        }
        for _ in range(20):
            start = time.perf_counter()
            raw = decode(text)
            t1 = time.perf_counter()
            nodes, _, _ = normalize(raw, "postgresql")
            t2 = time.perf_counter()
            findings, _ = analyze_nodes(nodes)
            t3 = time.perf_counter()
            canonical(
                {
                    "nodes": [n.model_dump(mode="json") for n in nodes],
                    "findings": [f.model_dump(mode="json") for f in findings],
                }
            )
            t4 = time.perf_counter()
            analyze_plan(text, "postgresql", "postgresql-json")
            t5 = time.perf_counter()
            for key, value in zip(
                samples, (t1 - start, t2 - t1, t3 - t2, t4 - t3, t5 - t4), strict=True
            ):
                samples[key].append(value * 1000)
        tracemalloc.start()
        analyze_plan(text, "postgresql", "postgresql-json")
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        results.append(
            {
                "fixture": name,
                "input_bytes": len(text.encode()),
                "nodes": len(nodes),
                "median_ms": {k: round(statistics.median(v), 3) for k, v in samples.items()},
                "peak_traced_bytes": peak,
            }
        )
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "iterations": 20,
                "notes": "Synthetic offline imports; stage serialization excludes final report hashing, total_ms measures full analyze_plan separately. Traced Python allocations are not process RSS.",
                "results": results,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
