import pytest

from core.envelope import EnvelopeContext
from core.envelope.registry import EnvelopeRegistry


class EnvelopeV2Builder:
    schema_version = "2.0"

    def build(self, payload, context: EnvelopeContext) -> dict:
        return {
            "schema_version": self.schema_version,
            "event_type": context.event_type,
            "origin": context.origin,
            "payload": payload,
        }


def test_registry_returns_registered_builder():
    registry = EnvelopeRegistry()
    registry.register(EnvelopeV2Builder())

    context = EnvelopeContext(
        schema_version="2.0",
        event_type="position",
        origin="test-origin",
        normalized=True,
        ingested_at_ms=1,
    )

    builder = registry.get("2.0")
    envelope = builder.build({"tag_id": "1"}, context)

    assert envelope["schema_version"] == "2.0"
    assert envelope["origin"] == "test-origin"
    assert envelope["payload"] == {"tag_id": "1"}


def test_registry_raises_for_unsupported_version():
    registry = EnvelopeRegistry()
    with pytest.raises(ValueError, match="Unsupported envelope version"):
        registry.get("9.9")
