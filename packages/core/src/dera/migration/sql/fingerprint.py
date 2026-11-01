"""SQL Artifact Fingerprint Calculator.

Produces an immutable SHA-256 semantic fingerprint over the canonical JSON representation
(RFC 8785) of the generated SQL artifact.

Excludes:
- Wall-clock timestamps.
- Volatile process IDs / transient machine metrics.
"""

import hashlib
import json
from typing import Any

from dera.migration.sql.enums import SqlDialectType
from dera.migration.sql.models import GeneratedSqlStatement, TransactionBlock


class SqlFingerprintCalculator:
    """Calculates deterministic SHA-256 fingerprints for SQL migration artifacts."""

    @classmethod
    def compute_artifact_fingerprint(
        cls,
        source_plan_fingerprint: str,
        dialect: SqlDialectType,
        compiler_version: str,
        statements: list[GeneratedSqlStatement],
        transaction_blocks: list[TransactionBlock],
    ) -> str:
        """Compute canonical SQL artifact fingerprint."""
        payload: dict[str, Any] = {
            "source_plan_fingerprint": source_plan_fingerprint,
            "dialect": dialect.value,
            "compiler_version": compiler_version,
            "statements": [
                {
                    "statement_id": s.statement_id,
                    "source_operation_id": s.source_operation_id,
                    "sql": s.sql,
                    "execution_mode": s.execution_mode.value,
                    "is_destructive": s.is_destructive,
                }
                for s in sorted(statements, key=lambda st: st.statement_id)
            ],
            "transaction_blocks": [
                {
                    "block_id": b.block_id,
                    "block_order": b.block_order,
                    "execution_mode": b.execution_mode.value,
                    "statement_ids": b.statement_ids,
                }
                for b in sorted(transaction_blocks, key=lambda tb: tb.block_order)
            ],
        }

        canonical_json = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
