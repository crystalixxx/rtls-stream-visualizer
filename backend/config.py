import os
from dataclasses import dataclass
from pathlib import Path

from core.config import (
    BackendApiConfig as ApiConfig,
    DatabaseConfig,
    RabbitMQConfig,
    load_config,
)


@dataclass(frozen=True)
class BackendConfig:
    api: ApiConfig
    database: DatabaseConfig
    rabbitmq: RabbitMQConfig


def load_backend_config(config_path: Path | None = None) -> BackendConfig:
    app_config = load_config(config_path, force_reload=config_path is not None)

    api_host = os.getenv("API_HOST", app_config.backend.api.host)
    api_port = int(os.getenv("API_PORT", str(app_config.backend.api.port)))
    dsn = os.getenv("DATABASE_DSN", app_config.database.dsn)
    rabbitmq_url = os.getenv("RABBITMQ_URL", app_config.rabbitmq.url)

    return BackendConfig(
        api=ApiConfig(host=api_host, port=api_port),
        database=DatabaseConfig(dsn=dsn),
        rabbitmq=RabbitMQConfig(
            url=rabbitmq_url,
            exchange=app_config.rabbitmq.exchange,
            exchange_type=app_config.rabbitmq.exchange_type,
            queue=app_config.rabbitmq.queue,
            routing_key=app_config.rabbitmq.routing_key,
        ),
    )
