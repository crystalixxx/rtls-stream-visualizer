from core.udp.server import UdpServer
from core.config import get_config


def start_udp():
    config = get_config()

    publisher = ...  # TODO: add explicit initialize of publisher for udp server

    server = UdpServer(
        config.udp_server.ip, config.udp_server.port, publisher, config.udp_server.topic
    )
    server.serve_forever()


if __name__ == "__main__":
    start_udp()
