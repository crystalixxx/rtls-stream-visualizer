from fastapi.testclient import TestClient

from backend.app import create_app
from backend.config import ApiConfig, BackendConfig, DatabaseConfig


def _config() -> BackendConfig:
    return BackendConfig(
        api=ApiConfig(host="127.0.0.1", port=8000),
        database=DatabaseConfig(dsn="postgresql://postgres:postgres@localhost:5432/db"),
    )


def test_health_returns_200_when_database_is_available(monkeypatch):
    monkeypatch.setattr("backend.api.health.probe_database", lambda config: True)
    client = TestClient(create_app(_config()))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_503_when_database_is_unavailable(monkeypatch):
    monkeypatch.setattr("backend.api.health.probe_database", lambda config: False)
    client = TestClient(create_app(_config()))

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}


def test_health_returns_503_when_database_probe_raises(monkeypatch):
    def _raise(_config):
        raise RuntimeError("db down")

    monkeypatch.setattr("backend.api.health.probe_database", _raise)
    client = TestClient(create_app(_config()))

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}
