from core.config import get_config
from core.udp.server import UdpServer
from core.validate import Validator
from stream_handler import LS1000Parser, JsonStreamNormalizer


def start_udp():
    config = get_config()

    publisher = ...  # TODO: add explicit initialize of publisher for udp server
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
    server.serve_forever()


if __name__ == "__main__":
    start_udp()
