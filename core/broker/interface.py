from typing import Protocol, Mapping


class BrockerPublisher(Protocol):
    def publish(
        self, topic: str, message: bytes, headers: Mapping[str, str] | None = None
    ) -> None: ...
