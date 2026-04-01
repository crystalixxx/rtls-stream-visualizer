from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.positions import router as positions_router
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


def _make_app() -> FastAPI:
    app = FastAPI()
    app.state.config = _config()
    app.state.pool = MagicMock()
    app.include_router(positions_router, prefix="/api/v1")
    return app


_ROWS = [
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
        "tag_id": "tag-001",
        "ts_utc_ms": 1700000001000,
        "source_type": "display",
        "status": None,
        "layer": 1,
        "area": "zone-A",
        "x": 11.0,
        "y": 21.0,
        "z": 0.0,
        "lng": None,
        "lat": None,
        "origin": "ls-1000",
    },
]


@patch("backend.api.positions.count_position_history", return_value=2)
@patch("backend.api.positions.get_position_history", return_value=_ROWS)
@patch("backend.api.positions.get_connection")
def test_history_returns_positions(mock_conn, mock_get, mock_count):
    client = TestClient(_make_app())

    response = client.get("/api/v1/positions/history?tag_id=tag-001")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert body["items"][0]["tag_id"] == "tag-001"


def test_history_requires_tag_id():
    client = TestClient(_make_app())

    response = client.get("/api/v1/positions/history")

    assert response.status_code == 422


@patch("backend.api.positions.count_position_history", return_value=0)
@patch("backend.api.positions.get_position_history", return_value=[])
@patch("backend.api.positions.get_connection")
def test_history_empty_result(mock_conn, mock_get, mock_count):
    client = TestClient(_make_app())

    response = client.get("/api/v1/positions/history?tag_id=unknown")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["items"] == []


@patch("backend.api.positions.count_position_history", return_value=50)
@patch("backend.api.positions.get_position_history", return_value=[_ROWS[0]])
@patch("backend.api.positions.get_connection")
def test_history_pagination(mock_conn, mock_get, mock_count):
    client = TestClient(_make_app())

    response = client.get("/api/v1/positions/history?tag_id=tag-001&limit=1&offset=10")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 50
    assert len(body["items"]) == 1

    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert call_args[0][1] == "tag-001"
    assert call_args[0][4] == 1
    assert call_args[0][5] == 10


@patch("backend.api.positions.count_position_history", return_value=5)
@patch("backend.api.positions.get_position_history", return_value=_ROWS[:1])
@patch("backend.api.positions.get_connection")
def test_history_time_range_filter(mock_conn, mock_get, mock_count):
    client = TestClient(_make_app())

    response = client.get(
        "/api/v1/positions/history"
        "?tag_id=tag-001&from_ts=1700000000000&to_ts=1700000001000"
    )

    assert response.status_code == 200

    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert call_args[0][2] == 1700000000000
    assert call_args[0][3] == 1700000001000


def test_history_limit_validation():
    client = TestClient(_make_app())

    response = client.get("/api/v1/positions/history?tag_id=t&limit=0")
    assert response.status_code == 422

    response = client.get("/api/v1/positions/history?tag_id=t&limit=1001")
    assert response.status_code == 422


def test_history_offset_validation():
    client = TestClient(_make_app())

    response = client.get("/api/v1/positions/history?tag_id=t&offset=-1")
    assert response.status_code == 422
