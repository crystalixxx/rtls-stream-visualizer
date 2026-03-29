import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class Broadcast:
    """In-process pub/sub for pushing position updates to WebSocket clients.

    Each subscriber gets its own bounded asyncio.Queue. Messages that cannot
    be delivered (queue full) are silently dropped to prevent slow clients
    from back-pressuring the consumer pipeline.
    """

    def __init__(self, maxsize: int = 256) -> None:
        self._maxsize = maxsize
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(
            maxsize=self._maxsize,
        )
        self._subscribers.add(queue)
        logger.debug("New subscriber, total=%d", len(self._subscribers))
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(queue)
        logger.debug("Subscriber removed, total=%d", len(self._subscribers))

    async def publish(self, envelope: dict[str, Any]) -> None:
        for queue in self._subscribers:
            try:
                queue.put_nowait(envelope)
            except asyncio.QueueFull:
                logger.warning("Subscriber queue full, dropping message")

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
