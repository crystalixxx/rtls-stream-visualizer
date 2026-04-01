import logging

from core.broker.rabbitmq import RabbitMQPublisher
from core.config import get_config
from core.tracing import get_otlp_endpoint, init_tracing
from core.udp.server import UdpServer
from core.validate import Validator
from stream_handler import LS1000Parser, JsonStreamNormalizer

logger = logging.getLogger(__name__)


def start_udp():
    config = get_config()
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
