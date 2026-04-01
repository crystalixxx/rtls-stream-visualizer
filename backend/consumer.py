import asyncio
import json
import logging
import signal
from functools import partial

import aio_pika
from psycopg_pool import ConnectionPool

from backend.config import load_backend_config, BackendConfig
from backend.db import create_pool, get_connection
from backend.repository import persist_envelope

logger = logging.getLogger(__name__)


async def on_message(
    message: aio_pika.abc.AbstractIncomingMessage,
    pool: ConnectionPool,
    loop: asyncio.AbstractEventLoop,
) -> None:
    async with message.process(requeue=True):
        body = message.body
        try:
            envelope = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error("Malformed message, dropping: %s", exc)
            return

        payload = envelope.get("payload")
        if not isinstance(payload, dict) or "tag_id" not in payload:
            logger.error("Envelope missing payload.tag_id, dropping")
            return

        try:
            await loop.run_in_executor(None, partial(_write_to_db, pool, envelope))
        except Exception:
            logger.exception("DB write failed for tag_id=%s", payload.get("tag_id"))
            raise


def _write_to_db(pool: ConnectionPool, envelope: dict) -> None:
    with get_connection(pool) as connection:
        persist_envelope(connection, envelope)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = load_backend_config()
    pool = create_pool(config)
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    connection = await aio_pika.connect_robust(config.rabbitmq.url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            config.rabbitmq.exchange,
            aio_pika.ExchangeType(config.rabbitmq.exchange_type),
            durable=True,
        )

        queue = await channel.declare_queue(config.rabbitmq.queue, durable=True)
        await queue.bind(exchange, routing_key=config.rabbitmq.routing_key)

        callback = partial(on_message, pool=pool, loop=loop)
        await queue.consume(callback)

        logger.info(
            "Consumer started: exchange=%s queue=%s routing_key=%s",
            config.rabbitmq.exchange,
            config.rabbitmq.queue,
            config.rabbitmq.routing_key,
        )

        await stop_event.wait()

    pool.close()
    logger.info("Consumer shut down")


if __name__ == "__main__":
    asyncio.run(main())
