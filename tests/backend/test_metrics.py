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


def test_metrics_returns_200(monkeypatch):
    monkeypatch.setattr("backend.api.health.probe_database", lambda config: True)
    client = TestClient(create_app(_config()))

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_metrics_contains_expected_counters(monkeypatch):
    monkeypatch.setattr("backend.api.health.probe_database", lambda config: True)
    client = TestClient(create_app(_config()))

    response = client.get("/metrics")
    body = response.text

    assert "http_requests_total" in body
    assert "ws_active_connections" in body
    assert "consumer_messages_processed_total" in body
    assert "db_write_duration_seconds" in body
