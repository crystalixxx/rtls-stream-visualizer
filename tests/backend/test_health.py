from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.app import create_app
from backend.config import ApiConfig, BackendConfig, DatabaseConfig
from core.config import RabbitMQConfig


def _config() -> BackendConfig:
    return BackendConfig(
        api=ApiConfig(host="127.0.0.1", port=8000),
        database=DatabaseConfig(dsn="postgresql://postgres:postgres@localhost:5432/db"),
        rabbitmq=RabbitMQConfig(
            url="amqp://guest:guest@localhost:5672/",
            exchange="rtls",
            exchange_type="topic",
            queue="rtls.events",
            routing_key="rtls.events",
        ),
    )


def test_health_returns_200_when_database_is_available(monkeypatch):
    monkeypatch.setattr("backend.api.health.probe_database", lambda pool: True)
    app = create_app(_config())
    app.state.pool = MagicMock()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_503_when_database_is_unavailable(monkeypatch):
    monkeypatch.setattr("backend.api.health.probe_database", lambda pool: False)
    app = create_app(_config())
    app.state.pool = MagicMock()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}


def test_health_returns_503_when_database_probe_raises(monkeypatch):
    def _raise(_pool):
        raise RuntimeError("db down")

    monkeypatch.setattr("backend.api.health.probe_database", _raise)
    app = create_app(_config())
    app.state.pool = MagicMock()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}
