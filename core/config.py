import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


@dataclass(frozen=True)
class ValidationConfig:
    schema_path: Path


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    format: str


@dataclass(frozen=True)
class AppConfig:
    validation: ValidationConfig
    logging: LoggingConfig


_config: Optional[AppConfig] = None


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    global _config

    if _config is not None:
        return _config

    path = config_path or DEFAULT_CONFIG_PATH

    logger.debug("Loading configuration from: %s", path)

    with open(path, "r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file)

    validation_config = ValidationConfig(
        schema_path=_resolve_path(raw_config["validation"]["schema_path"])
    )

    logging_config = LoggingConfig(
        level=raw_config["logging"]["level"], format=raw_config["logging"]["format"]
    )

    _config = AppConfig(validation=validation_config, logging=logging_config)

    logger.info("Configuration loaded successfully")

    return _config


def get_config() -> AppConfig:
    if _config is None:
        return load_config()

    return _config
