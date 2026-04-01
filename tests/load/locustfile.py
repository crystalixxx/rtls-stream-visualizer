"""Locust load-test scenarios for the RTLS backend.

Covers two user types:

* ``HistoryUser``   -- hammers ``GET /api/v1/positions/history``
* ``WebSocketUser`` -- opens a persistent WS connection and measures message
  delivery latency / dropped-message rate

Run::

    locust -f tests/load/locustfile.py --host http://localhost:8000
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from pathlib import Path

import locust
from locust import HttpUser, User, between, events, task
from locust.exception import StopUser

from tests.load.tag_pool import build_sequential_tag_pool, read_tag_pool

try:
    import websocket as _ws_mod  # websocket-client
except ImportError:
    _ws_mod = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost:8000")
LOAD_TAG_PREFIX = os.getenv("LOAD_TAG_PREFIX", "TAG")
LOAD_TAG_COUNT = int(os.getenv("LOAD_TAG_COUNT", "20"))
LOAD_TAG_WIDTH = int(os.getenv("LOAD_TAG_WIDTH", "4"))
_TAG_POOL_CANDIDATES = (
    os.getenv("LOAD_TAG_STATE_FILE"),
    "tests/load/.active_tags.json",
    "/mnt/locust/.active_tags.json",
)
_TAG_POOL_CACHE: list[str] | None = None
_TAG_POOL_MTIME_NS: int | None = None


def _default_tag_pool() -> list[str]:
    return build_sequential_tag_pool(
        LOAD_TAG_COUNT,
        prefix=LOAD_TAG_PREFIX,
        width=LOAD_TAG_WIDTH,
    )


def _load_tag_pool_from_file() -> list[str] | None:
    global _TAG_POOL_CACHE, _TAG_POOL_MTIME_NS

    for raw_path in _TAG_POOL_CANDIDATES:
        if not raw_path:
            continue
        path = Path(raw_path)
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue

        if _TAG_POOL_CACHE is not None and _TAG_POOL_MTIME_NS == stat.st_mtime_ns:
            return _TAG_POOL_CACHE

        try:
            tags = read_tag_pool(path)
        except (OSError, ValueError) as exc:
            logger.warning("Failed to load active tag pool from %s: %s", path, exc)
            continue

        _TAG_POOL_CACHE = tags
        _TAG_POOL_MTIME_NS = stat.st_mtime_ns
        logger.info("Loaded %d active tags from %s", len(tags), path)
        return tags

    return _TAG_POOL_CACHE


def _get_tag_pool() -> list[str]:
    tags = _load_tag_pool_from_file()
    if tags:
        return tags
    return _default_tag_pool()


# ---------------------------------------------------------------------------
# REST: GET /api/v1/positions/history
# ---------------------------------------------------------------------------


class HistoryUser(HttpUser):
    """Simulates clients fetching position history via the REST API."""

    wait_time = between(0.1, 1.0)

    @task(3)
    def get_history_default(self) -> None:
        tag_id = random.choice(_get_tag_pool())
        self.client.get(
            "/api/v1/positions/history",
            params={"tag_id": tag_id, "limit": 100},
            name="/api/v1/positions/history",
        )

    @task(1)
    def get_history_with_time_range(self) -> None:
        tag_id = random.choice(_get_tag_pool())
        now_ms = int(time.time() * 1000)
        self.client.get(
            "/api/v1/positions/history",
            params={
                "tag_id": tag_id,
                "from_ts": now_ms - 600_000,
                "to_ts": now_ms,
                "limit": 500,
            },
            name="/api/v1/positions/history [time-range]",
        )

    @task(1)
    def get_health(self) -> None:
        self.client.get("/health", name="/health")


# ---------------------------------------------------------------------------
# WebSocket: /api/v1/ws/positions
# ---------------------------------------------------------------------------


class WebSocketUser(User):
    """Holds a WebSocket connection and tracks message delivery metrics.

    Requires the ``websocket-client`` package (``pip install websocket-client``).
    """

    wait_time = between(0.5, 2.0)

    def __init__(self, environment: locust.env.Environment) -> None:
        super().__init__(environment)
        self._ws: _ws_mod.WebSocket | None = None  # type: ignore[union-attr]
        self._received: int = 0
        self._dropped_estimate: int = 0

    def on_start(self) -> None:
        if _ws_mod is None:
            logger.error(
                "websocket-client is not installed; "
                "install it with: pip install websocket-client"
            )
            raise StopUser()

        host = self.environment.host or f"http://{BACKEND_HOST}"
        ws_url = host.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/api/v1/ws/positions"

        t0 = time.perf_counter()
        try:
            self._ws = _ws_mod.create_connection(ws_url, timeout=10)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            events.request.fire(
                request_type="WS",
                name="connect",
                response_time=elapsed_ms,
                response_length=0,
                exception=None,
                context={},
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            events.request.fire(
                request_type="WS",
                name="connect",
                response_time=elapsed_ms,
                response_length=0,
                exception=exc,
                context={},
            )
            raise StopUser() from exc

        self._read_snapshot()

    def _read_snapshot(self) -> None:
        """Read the initial snapshot (JSON array) sent right after connect."""
        t0 = time.perf_counter()
        try:
            raw = self._ws.recv()  # type: ignore[union-attr]
            data = json.loads(raw)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            length = len(raw) if isinstance(raw, (str, bytes)) else 0
            events.request.fire(
                request_type="WS",
                name="snapshot",
                response_time=elapsed_ms,
                response_length=length,
                exception=None,
                context={},
            )
            logger.debug("Snapshot received: %d positions", len(data))
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            events.request.fire(
                request_type="WS",
                name="snapshot",
                response_time=elapsed_ms,
                response_length=0,
                exception=exc,
                context={},
            )

    @task
    def receive_message(self) -> None:
        if self._ws is None:
            raise StopUser()

        self._ws.settimeout(5.0)
        t0 = time.perf_counter()
        try:
            raw = self._ws.recv()
            elapsed_ms = (time.perf_counter() - t0) * 1000
            envelope = json.loads(raw)

            ingested_at = envelope.get("ingested_at_ms")
            if ingested_at:
                delivery_latency = time.time() * 1000 - ingested_at
                events.request.fire(
                    request_type="WS",
                    name="delivery_latency",
                    response_time=delivery_latency,
                    response_length=len(raw),
                    exception=None,
                    context={},
                )

            events.request.fire(
                request_type="WS",
                name="recv",
                response_time=elapsed_ms,
                response_length=len(raw),
                exception=None,
                context={},
            )
            self._received += 1
        except _ws_mod.WebSocketTimeoutException:
            pass
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            events.request.fire(
                request_type="WS",
                name="recv",
                response_time=elapsed_ms,
                response_length=0,
                exception=exc,
                context={},
            )

    def on_stop(self) -> None:
        if self._ws is not None:
            self._ws.close()
            self._ws = None
        logger.info("WS user stopped, received %d messages", self._received)
