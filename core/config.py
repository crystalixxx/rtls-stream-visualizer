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
    origin: str
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
class BrokerConfig:
    envelope_version: str


@dataclass(frozen=True)
class AppConfig:
    validation: ValidationConfig
    logging: LoggingConfig
    udp_server: UdpServerConfig
    broker: BrokerConfig


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


def _load_raw_config(path: Path) -> Dict[str, Any]:
    logger.debug("Loading configuration from: %s", path)

    with open(path, "r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file)

    if not isinstance(raw_config, dict):
        raise TypeError("Config root must be a mapping (dict)")

    return raw_config


def _build_validation_config(raw_config: Dict[str, Any]) -> ValidationConfig:
    validation = raw_config.get("validation", {})
    if not isinstance(validation, Mapping):
        raise TypeError("validation section must be a mapping (dict)")

    schema_path = validation.get("schema_path")
    if schema_path is None:
        raise KeyError("validation section must include 'schema_path'")

    origin = _get_or_use_default(
        raw_config, ["validation", "origin"], "test-stream-json"
    )
    return ValidationConfig(
        origin=origin,
        schema_path=_resolve_path(schema_path),
    )


def _build_logging_config(raw_config: Dict[str, Any]) -> LoggingConfig:
    return LoggingConfig(
        level=raw_config["logging"]["level"], format=raw_config["logging"]["format"]
    )


def _build_udp_server_config(raw_config: Dict[str, Any]) -> UdpServerConfig:
    return UdpServerConfig(
        ip=raw_config["udp_server"]["ip"],
        port=raw_config["udp_server"]["port"],
        topic=_get_or_use_default(raw_config, ["udp_server", "topic"], "rtls.events"),
    )


def _build_broker_config(raw_config: Dict[str, Any]) -> BrokerConfig:
    return BrokerConfig(
        envelope_version=_get_or_use_default(
            raw_config, ["broker", "envelope_version"], "1.0"
        )
    )


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    global _config

    if _config is not None:
        return _config

    path = config_path or DEFAULT_CONFIG_PATH
    raw_config = _load_raw_config(path)

    validation_config = _build_validation_config(raw_config)
    logging_config = _build_logging_config(raw_config)
    udp_server = _build_udp_server_config(raw_config)
    broker_config = _build_broker_config(raw_config)

    _config = AppConfig(
        validation=validation_config,
        logging=logging_config,
        udp_server=udp_server,
        broker=broker_config,
    )

    logger.info("Configuration loaded successfully")

    return _config


def get_config() -> AppConfig:
    if _config is None:
        return load_config()

    return _config
