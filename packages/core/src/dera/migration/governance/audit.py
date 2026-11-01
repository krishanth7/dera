"""Append-Only Tamper-Evident Audit Evidence Logger.

Maintains a per-review cryptographic SHA-256 hash chain for all governance events.
Every event links to the preceding event hash, forming an audit chain.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional
from dera.migration.governance.models import AuditEvent


class AuditTrailManager:
    """Manages append-only cryptographic audit event chains."""

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    @classmethod
    def create_event(
        cls,
        review_id: str,
        workspace_id: str,
        actor_id: str,
        event_type: str,
        previous_state: Optional[str],
        new_state: str,
        artifact_fingerprint: str,
        policy_version: str,
        timestamp: str,
        payload: Dict[str, Any],
        previous_event_hash: Optional[str] = None,
    ) -> AuditEvent:
        """Construct a new audit event and advance the cryptographic hash chain."""
        prev_hash = previous_event_hash or cls.GENESIS_HASH

        # Canonical digest of payload
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload_digest = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()

        # Compute tamper-evident hash of event linking to prev_hash
        event_dict = {
            "review_id": review_id,
            "workspace_id": workspace_id,
            "actor_id": actor_id,
            "event_type": event_type,
            "previous_state": previous_state,
            "new_state": new_state,
            "artifact_fingerprint": artifact_fingerprint,
            "policy_version": policy_version,
            "timestamp": timestamp,
            "payload_digest": payload_digest,
            "previous_event_hash": prev_hash,
        }
        canonical_event = json.dumps(event_dict, sort_keys=True, separators=(",", ":"))
        event_hash = hashlib.sha256(canonical_event.encode("utf-8")).hexdigest()

        return AuditEvent(
            event_id=f"evt_{event_hash[:16]}",
            review_id=review_id,
            workspace_id=workspace_id,
            actor_id=actor_id,
            event_type=event_type,
            previous_state=previous_state,
            new_state=new_state,
            artifact_fingerprint=artifact_fingerprint,
            policy_version=policy_version,
            timestamp=timestamp,
            event_payload_digest=payload_digest,
            previous_event_hash=prev_hash,
            event_hash=event_hash,
        )

    @classmethod
    def verify_chain(cls, events: List[AuditEvent]) -> bool:
        """Verify unbroken cryptographic integrity of the event hash chain."""
        if not events:
            return True

        expected_prev = cls.GENESIS_HASH
        for evt in events:
            if evt.previous_event_hash != expected_prev:
                return False
            # Recompute event hash
            event_dict = {
                "review_id": evt.review_id,
                "workspace_id": evt.workspace_id,
                "actor_id": evt.actor_id,
                "event_type": evt.event_type,
                "previous_state": evt.previous_state,
                "new_state": evt.new_state,
                "artifact_fingerprint": evt.artifact_fingerprint,
                "policy_version": evt.policy_version,
                "timestamp": evt.timestamp,
                "payload_digest": evt.event_payload_digest,
                "previous_event_hash": evt.previous_event_hash,
            }
            canonical_event = json.dumps(event_dict, sort_keys=True, separators=(",", ":"))
            computed_hash = hashlib.sha256(canonical_event.encode("utf-8")).hexdigest()
            if computed_hash != evt.event_hash:
                return False
            expected_prev = evt.event_hash

        return True
