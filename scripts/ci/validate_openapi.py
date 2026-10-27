"""DERA CI — OpenAPI Specification Governance & Breaking Change Detection.

Validates the live FastAPI OpenAPI schema against the committed snapshot in
docs/api/openapi.v1.json, detecting unreviewed drift and breaking API changes.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from dera_api.factory import create_app

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SNAPSHOT_PATH = REPO_ROOT / "docs" / "api" / "openapi.v1.json"


def get_deterministic_openapi_dict() -> dict[str, Any]:
    """Generates the OpenAPI dictionary with deterministic sorting."""
    app = create_app()
    return app.openapi()


def serialize_openapi_json(data: dict[str, Any]) -> str:
    """Formats OpenAPI specification with deterministic indentation and sorted keys."""
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def detect_breaking_changes(baseline: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """Compares baseline vs current OpenAPI specs and flags breaking changes."""
    breaking_issues: list[str] = []

    base_paths = baseline.get("paths", {})
    curr_paths = current.get("paths", {})

    # 1. Removed paths
    for path in base_paths:
        if path not in curr_paths:
            breaking_issues.append(f"Removed endpoint path: '{path}'")
            continue

        # 2. Removed HTTP methods
        base_methods = base_paths[path]
        curr_methods = curr_paths[path]
        for method in base_methods:
            if method.lower() not in curr_methods:
                breaking_issues.append(
                    f"Removed HTTP method '{method.upper()}' on endpoint '{path}'"
                )
                continue

            base_op = base_methods[method]
            curr_op = curr_methods[method]

            # 3. Newly required query or header parameters
            base_params = {
                p["name"]: p
                for p in base_op.get("parameters", [])
                if isinstance(p, dict) and "name" in p
            }
            curr_params = {
                p["name"]: p
                for p in curr_op.get("parameters", [])
                if isinstance(p, dict) and "name" in p
            }

            for p_name, p_data in curr_params.items():
                if p_data.get("required", False):
                    if p_name not in base_params:
                        breaking_issues.append(
                            f"Added new required parameter '{p_name}' to {method.upper()} {path}"
                        )
                    elif not base_params[p_name].get("required", False):
                        breaking_issues.append(
                            f"Parameter '{p_name}' changed from optional to required in {method.upper()} {path}"
                        )

            # 4. Removed success response status codes
            base_responses = base_op.get("responses", {})
            curr_responses = curr_op.get("responses", {})
            for status_code in base_responses:
                if status_code.startswith("2") and status_code not in curr_responses:
                    breaking_issues.append(
                        f"Removed success status code '{status_code}' from {method.upper()} {path}"
                    )

    return breaking_issues


def main() -> int:
    parser = argparse.ArgumentParser(description="DERA OpenAPI Snapshot & Compatibility Validator")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check that live OpenAPI specification matches committed snapshot.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update committed docs/api/openapi.v1.json with current live schema.",
    )
    parser.add_argument(
        "--snapshot-path",
        type=Path,
        default=DEFAULT_SNAPSHOT_PATH,
        help="Path to openapi.v1.json snapshot.",
    )

    args = parser.parse_args()
    snapshot_path: Path = args.snapshot_path

    live_schema = get_deterministic_openapi_dict()
    live_json = serialize_openapi_json(live_schema)

    if args.update:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(live_json, encoding="utf-8")
        print(f"[SUCCESS] Updated OpenAPI snapshot at {snapshot_path}")
        return 0

    if not snapshot_path.exists():
        print(
            f"[ERROR] OpenAPI snapshot not found at {snapshot_path}. Run with --update to generate.",
            file=sys.stderr,
        )
        return 1

    snapshot_json = snapshot_path.read_text(encoding="utf-8")
    try:
        baseline_schema = json.loads(snapshot_json)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Corrupted JSON in {snapshot_path}: {e}", file=sys.stderr)
        return 1

    # Breaking change detection
    breaking_changes = detect_breaking_changes(baseline_schema, live_schema)
    if breaking_changes:
        print("\n[BREAKING API CHANGES DETECTED]:", file=sys.stderr)
        for issue in breaking_changes:
            print(f"  - {issue}", file=sys.stderr)
        return 2

    # Semantic equality check
    if live_json != serialize_openapi_json(baseline_schema):
        print(
            f"\n[DRIFT DETECTED] Live OpenAPI schema differs from {snapshot_path}.",
            file=sys.stderr,
        )
        print("Run 'python scripts/ci/validate_openapi.py --update' to sync.", file=sys.stderr)
        return 1

    print("[SUCCESS] OpenAPI specification matches committed snapshot with zero drift.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
