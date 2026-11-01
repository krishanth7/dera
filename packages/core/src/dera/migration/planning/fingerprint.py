"""Plan Fingerprint Calculator.

Produces an immutable SHA-256 semantic fingerprint over the canonical JSON representation
(RFC 8785) of the planned operations, dependencies, stages, and policies.

Excludes:
- Wall-clock timestamps.
- Volatile process IDs / transient machine metrics.
"""

import hashlib
import json
from typing import Any, Dict, List
from dera.migration.planning.models import AbstractMigrationOperation, PlanningStage


class PlanFingerprintCalculator:
    """Calculates deterministic SHA-256 fingerprints for migration plans."""

    @classmethod
    def compute_fingerprint(
        cls,
        comparison_fingerprint: str,
        risk_report_fingerprint: str,
        engine: str,
        policy_version: str,
        catalog_version: str,
        operations: List[AbstractMigrationOperation],
        stages: List[PlanningStage],
    ) -> str:
        """Compute canonical plan fingerprint."""
        payload: Dict[str, Any] = {
            "comparison_fingerprint": comparison_fingerprint,
            "risk_report_fingerprint": risk_report_fingerprint,
            "engine": engine.lower(),
            "policy_version": policy_version,
            "catalog_version": catalog_version,
            "operations": [
                {
                    "operation_id": op.operation_id,
                    "operation_type": op.operation_type.value,
                    "target_object_id": op.target_object_id,
                    "source_change_fingerprint": op.source_change_fingerprint,
                    "prerequisites": sorted(op.prerequisite_operation_ids),
                    "is_blocked": op.is_blocked,
                    "engine_capability": op.engine_capability.value,
                }
                for op in sorted(operations, key=lambda o: o.operation_id)
            ],
            "stages": [
                {
                    "stage_id": s.stage_id,
                    "stage_type": s.stage_type.value,
                    "stage_order": s.stage_order,
                    "operation_ids": s.operation_ids,
                }
                for s in sorted(stages, key=lambda st: st.stage_order)
            ],
        }

        # Canonical RFC 8785 JSON representation
        canonical_json = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
