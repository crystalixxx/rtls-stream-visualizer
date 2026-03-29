import asyncio
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.ws import router as ws_router
from backend.broadcast import Broadcast
from backend.config import BackendConfig
from core.config import BackendApiConfig, DatabaseConfig, RabbitMQConfig


def _config() -> BackendConfig:
    return BackendConfig(
        api=BackendApiConfig(host="127.0.0.1", port=8000),
        database=DatabaseConfig(dsn="postgresql://test:test@localhost:5432/test"),
        rabbitmq=RabbitMQConfig(
            url="amqp://guest:guest@localhost:5672/",
            exchange="rtls",
            exchange_type="topic",
            queue="rtls.events",
            routing_key="rtls.events",
        ),
    )


def _make_app(broadcast: Broadcast | None = None) -> FastAPI:
    app = FastAPI()
    app.state.config = _config()
    app.state.broadcast = broadcast or Broadcast()
    app.include_router(ws_router, prefix="/api/v1")
    return app


_SNAPSHOT = [
    {
        "tag_id": "tag-001",
        "ts_utc_ms": 1700000000000,
        "source_type": "display",
        "status": None,
        "layer": 1,
        "area": "zone-A",
        "x": 10.5,
        "y": 20.3,
        "z": 0.0,
        "lng": None,
        "lat": None,
        "origin": "ls-1000",
    },
    {
        "tag_id": "tag-002",
        "ts_utc_ms": 1700000001000,
        "source_type": "json",
        "status": None,
        "layer": 2,
        "area": "zone-B",
        "x": 5.0,
        "y": 15.0,
        "z": 1.0,
        "lng": 37.6,
        "lat": 55.7,
        "origin": "json",
    },
]


@patch("backend.api.ws.get_all_current_positions", return_value=_SNAPSHOT)
@patch("backend.api.ws.get_connection")
def test_ws_receives_snapshot_on_connect(mock_conn, mock_get_all):
    app = _make_app()
    client = TestClient(app)

    with client.websocket_connect("/api/v1/ws/positions") as ws:
        data = ws.receive_json()

    assert data == _SNAPSHOT
    mock_get_all.assert_called_once()


@patch("backend.api.ws.get_all_current_positions", return_value=[])
@patch("backend.api.ws.get_connection")
def test_ws_receives_live_update(mock_conn, mock_get_all):
    broadcast = Broadcast()
    app = _make_app(broadcast)
    client = TestClient(app)

    envelope = {"payload": {"tag_id": "tag-live"}, "event_type": "position"}

    with client.websocket_connect("/api/v1/ws/positions") as ws:
        snapshot = ws.receive_json()
        assert snapshot == []

        asyncio.get_event_loop().run_until_complete(broadcast.publish(envelope))

        update = ws.receive_json()
        assert update == envelope


@patch("backend.api.ws.get_all_current_positions", return_value=[])
@patch("backend.api.ws.get_connection")
def test_ws_disconnect_unsubscribes(mock_conn, mock_get_all):
    broadcast = Broadcast()
    app = _make_app(broadcast)
    client = TestClient(app)

    with client.websocket_connect("/api/v1/ws/positions") as ws:
        ws.receive_json()
        assert broadcast.subscriber_count == 1

    assert broadcast.subscriber_count == 0


@patch("backend.api.ws.get_all_current_positions", return_value=[])
@patch("backend.api.ws.get_connection")
def test_ws_empty_snapshot(mock_conn, mock_get_all):
    app = _make_app()
    client = TestClient(app)

    with client.websocket_connect("/api/v1/ws/positions") as ws:
        data = ws.receive_json()

    assert data == []
