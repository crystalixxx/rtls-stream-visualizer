import asyncio
import json
import logging
import time as _time
from contextlib import asynccontextmanager
from functools import partial

import aio_pika
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import context as otel_context, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from backend.api.health import router as health_router
from backend.api.metrics import router as metrics_router
from backend.api.positions import router as positions_router
from backend.api.ws import router as ws_router
from backend.broadcast import Broadcast
from backend.config import BackendConfig, load_backend_config
from backend.db import get_connection
from backend.metrics import (
    CONSUMER_MESSAGES_FAILED,
    CONSUMER_MESSAGES_PROCESSED,
    DB_WRITE_LATENCY,
    HTTP_REQUEST_COUNT,
    HTTP_REQUEST_LATENCY,
)
from backend.repository import persist_envelope
from core.tracing import extract_from_headers, get_otlp_endpoint, init_tracing

logger = logging.getLogger(__name__)

_CONSUMER_RETRY_DELAY = 5
_tracer = trace.get_tracer(__name__)


async def _on_message(
    message: aio_pika.abc.AbstractIncomingMessage,
    config: BackendConfig,
    broadcast: Broadcast,
    loop: asyncio.AbstractEventLoop,
) -> None:
    async with message.process(requeue=True):
        body = message.body
        try:
            envelope = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error("Malformed message, dropping: %s", exc)
            CONSUMER_MESSAGES_FAILED.labels(reason="malformed_json").inc()
            return

        payload = envelope.get("payload")
        if not isinstance(payload, dict) or "tag_id" not in payload:
            logger.error("Envelope missing payload.tag_id, dropping")
            CONSUMER_MESSAGES_FAILED.labels(reason="missing_tag_id").inc()
            return

        parent_ctx = extract_from_headers(message.headers or {})
        token = otel_context.attach(parent_ctx)
        try:
            with _tracer.start_as_current_span(
                "consume_message",
                attributes={"tag.id": payload.get("tag_id", "")},
            ):
                try:
                    with _tracer.start_as_current_span("db_write"):
                        t0 = _time.monotonic()
                        await loop.run_in_executor(
                            None, partial(_write_to_db, config, envelope)
                        )
                        DB_WRITE_LATENCY.observe(_time.monotonic() - t0)
                except Exception:
                    logger.exception(
                        "DB write failed for tag_id=%s", payload.get("tag_id")
                    )
                    CONSUMER_MESSAGES_FAILED.labels(reason="db_error").inc()
                    raise

                with _tracer.start_as_current_span("broadcast"):
                    await broadcast.publish(envelope)

                CONSUMER_MESSAGES_PROCESSED.inc()
        finally:
            otel_context.detach(token)


def _write_to_db(config: BackendConfig, envelope: dict) -> None:
    with get_connection(config) as connection:
        persist_envelope(connection, envelope)


async def _run_consumer(
    config: BackendConfig,
    broadcast: Broadcast,
    stop_event: asyncio.Event,
) -> None:
    """Connect to RabbitMQ and consume messages.

    Retries indefinitely on connection failure so the API can serve
    HTTP requests even when the broker is temporarily unavailable.
    """
    loop = asyncio.get_running_loop()
    connection: aio_pika.abc.AbstractRobustConnection | None = None

    while not stop_event.is_set():
        try:
            connection = await aio_pika.connect_robust(config.rabbitmq.url)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)

            exchange = await channel.declare_exchange(
                config.rabbitmq.exchange,
                aio_pika.ExchangeType(config.rabbitmq.exchange_type),
                durable=True,
            )

            queue = await channel.declare_queue(config.rabbitmq.queue, durable=True)
            await queue.bind(exchange, routing_key=config.rabbitmq.routing_key)

            callback = partial(
                _on_message, config=config, broadcast=broadcast, loop=loop
            )
            await queue.consume(callback)

            logger.info(
                "Embedded consumer started: exchange=%s queue=%s routing_key=%s",
                config.rabbitmq.exchange,
                config.rabbitmq.queue,
                config.rabbitmq.routing_key,
            )

            await stop_event.wait()
            break

        except Exception:
            logger.warning(
                "RabbitMQ connection failed, retrying in %ds",
                _CONSUMER_RETRY_DELAY,
                exc_info=True,
            )
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=_CONSUMER_RETRY_DELAY)
                break
            except asyncio.TimeoutError:
                continue
        finally:
            if connection and not connection.is_closed:
                await connection.close()

    logger.info("Embedded consumer stopped")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    config: BackendConfig = app.state.config
    init_tracing("backend", get_otlp_endpoint())

    broadcast = Broadcast()
    app.state.broadcast = broadcast

    stop_event = asyncio.Event()
    consumer_task = asyncio.create_task(_run_consumer(config, broadcast, stop_event))

    yield

    stop_event.set()
    await consumer_task


def create_app(config: BackendConfig | None = None) -> FastAPI:
    resolved_config = config or load_backend_config()

    app = FastAPI(lifespan=_lifespan)
    app.state.config = resolved_config

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _prometheus_middleware(request: Request, call_next) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)
        t0 = _time.monotonic()
        response: Response = await call_next(request)
        elapsed = _time.monotonic() - t0
        endpoint = request.url.path
        HTTP_REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(
            elapsed
        )
        HTTP_REQUEST_COUNT.labels(
            method=request.method, endpoint=endpoint, status=response.status_code
        ).inc()
        return response

    app.include_router(health_router)
    app.include_router(metrics_router)
    app.include_router(positions_router, prefix="/api/v1")
    app.include_router(ws_router, prefix="/api/v1")

    FastAPIInstrumentor.instrument_app(app)

    return app


app = create_app()
