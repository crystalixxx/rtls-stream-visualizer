import logging
import os
from collections.abc import Mapping

from prometheus_client import start_http_server

from core.broker.rabbitmq import RabbitMQPublisher
from core.config import get_config
from core.tracing import get_otlp_endpoint, init_tracing
from core.udp.server import UdpServer
from core.validate import Validator
from stream_handler import LS1000Parser, JsonStreamNormalizer

logger = logging.getLogger(__name__)


def _metrics_enabled(env: Mapping[str, str]) -> bool:
    return env.get("PROMETHEUS_METRICS_ENABLED", "true").lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _start_metrics_server(
    env: Mapping[str, str] | None = None,
) -> tuple[str, int] | None:
    resolved_env = env or os.environ
    if not _metrics_enabled(resolved_env):
        logger.info("Prometheus metrics server disabled")
        return None

    host = resolved_env.get("PROMETHEUS_METRICS_HOST", "0.0.0.0")
    port = int(resolved_env.get("PROMETHEUS_METRICS_PORT", "9100"))
    start_http_server(port, addr=host)
    logger.info("Prometheus metrics server started on %s:%d", host, port)
    return host, port


def start_udp():
    config = get_config()
    _start_metrics_server()
    init_tracing("udp-receiver", get_otlp_endpoint())

    publisher = RabbitMQPublisher(config.rabbitmq)
    validator = Validator(config.validation.schema_path, config.validation.origin)
    parser = LS1000Parser()
    json_normalizer = JsonStreamNormalizer(config.validation.origin)

    server = UdpServer(
        config.udp_server.ip,
        config.udp_server.port,
        publisher,
        config.udp_server.topic,
        validator=validator,
        parser=parser,
        json_normalizer=json_normalizer,
        envelope_version=config.broker.envelope_version,
    )
    try:
        server.serve_forever()
    finally:
        server.close()
        publisher.close()
        logger.info("UDP receiver shut down")


if __name__ == "__main__":
    start_udp()
