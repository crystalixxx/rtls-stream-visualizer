import asyncio
import logging
import time as _time
import threading
from collections.abc import Mapping

import aio_pika
from prometheus_client import Counter, Histogram

from core.config import RabbitMQConfig

logger = logging.getLogger(__name__)

_PUBLISHER_MESSAGES_TOTAL = Counter(
    "publisher_messages_total",
    "Total messages published to RabbitMQ",
)
_PUBLISHER_LATENCY = Histogram(
    "publisher_publish_duration_seconds",
    "RabbitMQ publish latency in seconds",
)


class RabbitMQPublisher:
    """Sync publisher that bridges the BrockerPublisher protocol to aio-pika.

    Runs a dedicated asyncio event loop in a background daemon thread so that
    the synchronous ``UdpServer.serve_forever`` can call ``publish()`` without
    blocking on event-loop creation each time.
    """

    def __init__(self, config: RabbitMQConfig) -> None:
        self._config = config
        self._loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="rabbitmq-publisher"
        )
        self._thread.start()

        future = asyncio.run_coroutine_threadsafe(self._connect(), self._loop)
        future.result()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._config.url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            self._config.exchange,
            aio_pika.ExchangeType(self._config.exchange_type),
            durable=True,
        )
        logger.info(
            "RabbitMQ publisher connected: exchange=%s type=%s",
            self._config.exchange,
            self._config.exchange_type,
        )

    def publish(
        self,
        topic: str,
        message: bytes,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        future = asyncio.run_coroutine_threadsafe(
            self._publish(topic, message, headers),
            self._loop,
        )
        future.result()

    async def _publish(
        self,
        topic: str,
        message: bytes,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        amqp_message = aio_pika.Message(
            body=message,
            headers=dict(headers) if headers else None,
        )
        routing_key = topic or self._config.routing_key
        t0 = _time.monotonic()
        await self._exchange.publish(amqp_message, routing_key=routing_key)
        _PUBLISHER_LATENCY.observe(_time.monotonic() - t0)
        _PUBLISHER_MESSAGES_TOTAL.inc()
        logger.debug(
            "Published message to exchange=%s routing_key=%s size=%d",
            self._config.exchange,
            routing_key,
            len(message),
        )

    def close(self) -> None:
        if self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                self._close_connection(), self._loop
            )
            future.result(timeout=5)
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=5)
        logger.info("RabbitMQ publisher closed")

    async def _close_connection(self) -> None:
        await self._channel.close()
        await self._connection.close()
