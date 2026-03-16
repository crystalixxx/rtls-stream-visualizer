from core.envelope.base import EnvelopeBuilder
from core.envelope.v1 import EnvelopeV1Builder


class EnvelopeRegistry:
    def __init__(self):
        self._builders: dict[str, EnvelopeBuilder] = {}

    def register(self, builder: EnvelopeBuilder) -> None:
        self._builders[builder.schema_version] = builder

    def get(self, version: str) -> EnvelopeBuilder:
        builder = self._builders.get(version)
        if builder is None:
            supported = ", ".join(sorted(self._builders.keys())) or "<none>"
            raise ValueError(
                f"Unsupported envelope version '{version}'. Supported versions: {supported}"
            )
        return builder


def create_default_envelope_registry() -> EnvelopeRegistry:
    registry = EnvelopeRegistry()
    registry.register(EnvelopeV1Builder())
    return registry
