from pathlib import Path

from backend.config import load_backend_config

_YAML_TEMPLATE = """
validation:
  origin: "test-stream-json"
  schema_path: "config/some_device_scheme.json"
logging:
  level: "INFO"
  format: "%%(message)s"
udp_server:
  ip: "0.0.0.0"
  port: 9999
  topic: "rtls.events"
broker:
  envelope_version: "1.0"
rabbitmq:
  url: "amqp://guest:guest@localhost:5672/"
  exchange: "rtls"
  exchange_type: "topic"
  queue: "rtls.events"
  routing_key: "rtls.events"
backend:
  api:
    host: "{api_host}"
    port: {api_port}
database:
  dsn: "{dsn}"
"""


def _write_config(
    tmp_path,
    api_host="127.0.0.1",
    api_port=8000,
    dsn="postgresql://yaml-user:yaml-pass@localhost:5432/yaml-db",
):
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(
        _YAML_TEMPLATE.format(api_host=api_host, api_port=api_port, dsn=dsn),
        encoding="utf-8",
    )
    return config_path


def test_load_backend_config_reads_backend_values_from_yaml(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_DSN", raising=False)
    monkeypatch.delenv("RABBITMQ_URL", raising=False)
    config_path = _write_config(tmp_path, api_host="0.0.0.0", api_port=9000)

    config = load_backend_config(config_path)

    assert config.api.host == "0.0.0.0"
    assert config.api.port == 9000
    assert (
        config.database.dsn == "postgresql://yaml-user:yaml-pass@localhost:5432/yaml-db"
    )


def test_load_backend_config_overrides_database_dsn_from_environment(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DATABASE_DSN", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.delenv("RABBITMQ_URL", raising=False)
    config_path = _write_config(tmp_path)

    config = load_backend_config(config_path)

    assert config.database.dsn == "postgresql://user:pass@localhost:5432/db"


def test_load_backend_config_reads_rabbitmq_from_yaml(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_DSN", raising=False)
    monkeypatch.delenv("RABBITMQ_URL", raising=False)
    config_path = _write_config(tmp_path)

    config = load_backend_config(config_path)

    assert config.rabbitmq.url == "amqp://guest:guest@localhost:5672/"
    assert config.rabbitmq.exchange == "rtls"
    assert config.rabbitmq.exchange_type == "topic"
    assert config.rabbitmq.queue == "rtls.events"
    assert config.rabbitmq.routing_key == "rtls.events"


def test_load_backend_config_overrides_rabbitmq_url_from_environment(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("DATABASE_DSN", raising=False)
    monkeypatch.setenv("RABBITMQ_URL", "amqp://prod:secret@rabbit:5672/vhost")
    config_path = _write_config(tmp_path)

    config = load_backend_config(config_path)

    assert config.rabbitmq.url == "amqp://prod:secret@rabbit:5672/vhost"
    assert config.rabbitmq.exchange == "rtls"
