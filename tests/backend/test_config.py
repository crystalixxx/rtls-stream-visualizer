from pathlib import Path

from backend.config import load_backend_config


def test_load_backend_config_reads_backend_values_from_yaml(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_DSN", raising=False)
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(
        """
validation:
  origin: "test-stream-json"
  schema_path: "config/some_device_scheme.json"
logging:
  level: "INFO"
  format: "%(message)s"
udp_server:
  ip: "0.0.0.0"
  port: 9999
  topic: "rtls.events"
broker:
  envelope_version: "1.0"
backend:
  api:
    host: "0.0.0.0"
    port: 9000
database:
  dsn: "postgresql://yaml-user:yaml-pass@localhost:5432/yaml-db"
""",
        encoding="utf-8",
    )

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
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(
        """
validation:
  origin: "test-stream-json"
  schema_path: "config/some_device_scheme.json"
logging:
  level: "INFO"
  format: "%(message)s"
udp_server:
  ip: "0.0.0.0"
  port: 9999
  topic: "rtls.events"
broker:
  envelope_version: "1.0"
backend:
  api:
    host: "127.0.0.1"
    port: 8000
database:
  dsn: "postgresql://yaml-user:yaml-pass@localhost:5432/yaml-db"
""",
        encoding="utf-8",
    )

    config = load_backend_config(config_path)

    assert config.database.dsn == "postgresql://user:pass@localhost:5432/db"
