import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, List, Any, TypeVar, Mapping, cast

import yaml

T = TypeVar("T")

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
class UdpServerConfig:
    ip: str
    port: int
    topic: Optional[str]


@dataclass(frozen=True)
class AppConfig:
    validation: ValidationConfig
    logging: LoggingConfig
    udp_server: UdpServerConfig


_config: Optional[AppConfig] = None


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def _get_or_use_default(config: Dict[str, Any], path: List[str], default: Any) -> T:
    cur = config

    for key in path:
        if not isinstance(cur, Mapping):
            return default

        if key not in cur:
            return default

        cur = cur[key]

    if not isinstance(cur, type(default)):
        raise TypeError(
            f"Wrong type at {'.'.join(path)}: expected {type(default).__name__}, got {type(cur).__name__}"
        )

    return cast(T, cur)


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    global _config

    if _config is not None:
        return _config

    path = config_path or DEFAULT_CONFIG_PATH

    logger.debug("Loading configuration from: %s", path)

    with open(path, "r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file)

    if not isinstance(raw_config, dict):
        raise TypeError("Config root must be a mapping (dict)")

    validation_config = ValidationConfig(
        schema_path=_resolve_path(raw_config["validation"]["schema_path"])
    )

    logging_config = LoggingConfig(
        level=raw_config["logging"]["level"], format=raw_config["logging"]["format"]
    )

    udp_server = UdpServerConfig(
        ip=raw_config["udp_server"]["ip"],
        port=raw_config["udp_server"]["port"],
        topic=_get_or_use_default(
            raw_config, ["udp_server", "topic"], "rtls.events"
        ),  # TODO: Invent way to store default values
    )

    _config = AppConfig(
        validation=validation_config, logging=logging_config, udp_server=udp_server
    )

    logger.info("Configuration loaded successfully")

    return _config


def get_config() -> AppConfig:
    if _config is None:
        return load_config()

    return _config
