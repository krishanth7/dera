"""DERA Reverse Engineering — Phase 6.1 Deterministic Serialization & Deserialization.

Provides byte-level deterministic, canonical JSON serialization, SHA-256 fingerprint
generation, and safe reconstruction for SchemaRepresentation instances.

Guarantees:
- Reuses Phase 5.5 deterministic serialization conventions.
- Alphabetically sorted JSON keys (`sort_keys=True`).
- Explicit null handling and deterministic datetime formatting (ISO 8601 UTC with 'Z').
- Free of credentials or execution logic.
- Safe reconstruction via SchemaBuilder without arbitrary executable deserialization (no pickle/eval).
"""

from __future__ import annotations

import hashlib
import json

from pydantic import ValidationError

from dera.metadata.enums import MetadataCompleteness
from dera.metadata.models.database import CanonicalDatabase
from dera.metadata.serialization import _canonical_default_serializer
from dera.reverse_engineering.builder import SchemaBuilder, SchemaResourceLimits
from dera.reverse_engineering.capabilities import SchemaCapabilityProfile
from dera.reverse_engineering.errors import (
    SchemaResourceLimitError,
    SchemaSerializationError,
    UnsupportedSchemaContractError,
)
from dera.reverse_engineering.schema import (
    SCHEMA_REPRESENTATION_CONTRACT_VERSION,
    SchemaRepresentation,
)


def serialize_schema_representation(
    schema: SchemaRepresentation,
    indent: int | None = 2,
) -> str:
    """Serialize a SchemaRepresentation to deterministic UTF-8 JSON.

    Guarantees:
    - Sorted keys at all dictionary levels.
    - Deterministic date/time formatting with UTC 'Z'.
    - Explicit null representation for empty fields.
    - No credentials.
    """
    try:
        raw_dict = schema.to_dict()
        return json.dumps(
            raw_dict,
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
            default=_canonical_default_serializer,
        )
    except Exception as exc:
        raise SchemaSerializationError(f"Failed to serialize schema representation: {exc}") from exc


def compute_schema_hash(schema: SchemaRepresentation) -> str:
    """Compute a deterministic SHA-256 fingerprint over compact canonical JSON bytes.

    Digests are stable across runtime executions and invariant to formatting whitespace.
    """
    try:
        compact_json = json.dumps(
            schema.to_dict(),
            indent=None,
            separators=(",", ":"),
            sort_keys=True,
            ensure_ascii=False,
            default=_canonical_default_serializer,
        )
        return hashlib.sha256(compact_json.encode("utf-8")).hexdigest()
    except Exception as exc:
        raise SchemaSerializationError(f"Failed to compute schema hash: {exc}") from exc


def deserialize_schema_representation(
    json_str: str,
    limits: SchemaResourceLimits | None = None,
    workspace_id: str | None = None,
    strict_validation: bool = False,
) -> SchemaRepresentation:
    """Safely reconstruct a SchemaRepresentation from a serialized canonical JSON string.

    Validates:
    - JSON payload structure.
    - Contract version compatibility.
    - Resource bounds (payload length, object count).
    - Re-establishes ObjectRegistry with kind-verified lookup and duplicate protection.

    Does NOT deserialize arbitrary executable code.
    """
    if limits is None:
        limits = SchemaResourceLimits()

    payload_bytes = len(json_str.encode("utf-8"))
    if payload_bytes > limits.max_definition_bytes * 50:  # Bound serialized payload
        raise SchemaResourceLimitError(
            "max_serialized_payload_bytes",
            limits.max_definition_bytes * 50,
            payload_bytes,
        )

    try:
        data = json.loads(json_str)
    except Exception as exc:
        raise SchemaSerializationError(f"Malformed JSON schema payload: {exc}") from exc

    if not isinstance(data, dict):
        raise SchemaSerializationError(
            "Serialized schema payload must be a JSON object dictionary."
        )

    contract_version = data.get("contract_version")
    if contract_version != SCHEMA_REPRESENTATION_CONTRACT_VERSION:
        raise UnsupportedSchemaContractError(
            f"Unsupported schema contract version: {contract_version!r}. "
            f"Expected: {SCHEMA_REPRESENTATION_CONTRACT_VERSION!r}."
        )

    # Extract the database sub-model
    db_data = data.get("database")
    if not isinstance(db_data, dict):
        raise SchemaSerializationError(
            "Serialized schema representation missing 'database' dictionary."
        )

    canonical_db = CanonicalDatabase.model_validate(db_data)

    # Reconstruct via SchemaBuilder to guarantee complete registry, ordering, and validation
    schema = SchemaBuilder.from_canonical_database(
        database=canonical_db,
        workspace_id=workspace_id,
        limits=limits,
        strict_validation=strict_validation,
    )

    # Connector visibility cannot be inferred from the canonical database alone.
    # Validate the saved assessment before restoring it onto the rebuilt schema.
    try:
        completeness = MetadataCompleteness(data.get("completeness", schema.completeness))
        profile_data = data.get("capability_profile", schema.capability_profile)
        profile = (
            SchemaCapabilityProfile.model_validate(profile_data)
            if profile_data is not None
            else None
        )
    except (ValidationError, ValueError) as exc:
        raise SchemaSerializationError(f"Invalid serialized capability assessment: {exc}") from exc
    if profile is not None:
        if profile.engine != canonical_db.engine.strip().lower():
            raise SchemaSerializationError("Capability profile engine does not match the database.")
        if profile.overall_completeness != completeness:
            raise SchemaSerializationError(
                "Capability profile and schema completeness do not match."
            )
    return schema.model_copy(update={"capability_profile": profile, "completeness": completeness})


__all__ = [
    "compute_schema_hash",
    "deserialize_schema_representation",
    "serialize_schema_representation",
]
