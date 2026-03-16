from typing import Any

from core.envelope.base import EnvelopeBuilder, EnvelopeContext


class EnvelopeV1Builder(EnvelopeBuilder):
    schema_version = "1.0"

    def build(self, payload: Any, context: EnvelopeContext) -> dict:
        return {
            "schema_version": self.schema_version,
            "event_type": context.event_type,
            "origin": context.origin,
            "normalized": context.normalized,
            "ingested_at_ms": context.ingested_at_ms,
            "payload": payload,
        }
