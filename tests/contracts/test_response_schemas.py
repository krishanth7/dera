"""Tests for DERA API response schemas and serialization envelopes (Phase 4.2)."""

from __future__ import annotations

import json
import unittest
from datetime import UTC

from dera_api.contracts.base import CollectionEnvelope, DataEnvelope, DeraBaseModel
from dera_api.contracts.metadata import ResponseMetadata


class ItemModel(DeraBaseModel):
    """Test item schema."""

    id: str
    name: str
    status: str = "active"


import dera


class TestResponseSchemas(unittest.TestCase):
    """Validate response envelope models, metadata, and deterministic serialization."""

    def test_response_metadata_defaults(self) -> None:
        """Verify default metadata generates UTC timestamp and version."""
        meta = ResponseMetadata()
        self.assertEqual(meta.version, dera.__version__)
        self.assertEqual(meta.timestamp.tzinfo, UTC)
        self.assertIsNone(meta.request_id)

    def test_response_metadata_with_request_id(self) -> None:
        """Verify metadata retains explicit request ID."""
        req_id = "req-12345678-abcd"
        meta = ResponseMetadata(request_id=req_id)
        self.assertEqual(meta.request_id, req_id)
        serialized = meta.model_dump()
        self.assertEqual(serialized["request_id"], req_id)
        self.assertIn("timestamp", serialized)
        self.assertEqual(serialized["version"], dera.__version__)

    def test_data_envelope_single_resource(self) -> None:
        """Verify DataEnvelope[T] cleanly wraps resource payload with meta."""
        item = ItemModel(id="sch_1", name="public_schema")
        meta = ResponseMetadata(request_id="req-999")
        envelope = DataEnvelope[ItemModel](data=item, meta=meta)

        dump = envelope.model_dump()
        self.assertEqual(dump["data"]["id"], "sch_1")
        self.assertEqual(dump["data"]["name"], "public_schema")
        self.assertEqual(dump["data"]["status"], "active")
        self.assertEqual(dump["meta"]["request_id"], "req-999")

        # Verify JSON serialization is deterministic
        json_str = envelope.model_dump_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["data"]["name"], "public_schema")

    def test_collection_envelope(self) -> None:
        """Verify CollectionEnvelope wraps lists and computes count."""
        items = [
            ItemModel(id="1", name="Alpha"),
            ItemModel(id="2", name="Beta"),
            ItemModel(id="3", name="Gamma"),
        ]
        meta = ResponseMetadata(request_id="req-coll-1")
        envelope = CollectionEnvelope[ItemModel].create(items=items, meta=meta)

        self.assertEqual(envelope.count, 3)
        self.assertEqual(len(envelope.data), 3)
        self.assertEqual(envelope.meta.request_id, "req-coll-1")

    def test_collection_envelope_empty(self) -> None:
        """Verify CollectionEnvelope handles empty lists correctly."""
        envelope = CollectionEnvelope[ItemModel].create(items=[])
        self.assertEqual(envelope.count, 0)
        self.assertEqual(envelope.data, [])
        self.assertEqual(envelope.meta.version, dera.__version__)
