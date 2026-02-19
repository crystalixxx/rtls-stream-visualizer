from dataclasses import dataclass
from typing import Protocol, Any


@dataclass(frozen=True)
class EnvelopeContext:
    schema_version: str
    event_type: str
    origin: str
    normalized: bool
    ingested_at_ms: int


class EnvelopeBuilder(Protocol):
    schema_version: str

    def build(self, payload: Any, context: EnvelopeContext) -> dict: ...
