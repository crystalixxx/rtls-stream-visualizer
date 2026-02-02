import logging
import json
import socket
from collections.abc import Callable

from core.broker.interface import BrockerPublisher
from core.validate import Validator

logger = logging.getLogger(__name__)


class UdpServer:
    def __init__(
        self,
        ip: str,
        port: int,
        publisher: BrockerPublisher,
        topic: str,
        max_datagram_bytes: int = 64 * 1024,
        validator: Validator | None = None,
        on_decode_error: Callable[[bytes, Exception], None] | None = None,
    ):
        self.ip = ip
        self.port = port
        self.publisher = publisher
        self.topic = topic
        self.max_datagram_bytes = max_datagram_bytes
        self.validator = validator
        self.on_decode_error = on_decode_error

        logger.info(f"Creating UDP server {self.ip}:{self.port}")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))

    def serve_forever(self) -> None:
        while True:
            try:
                data, addr = self.socket.recvfrom(self.max_datagram_bytes)
            except OSError:
                break

            try:
                message = data
                headers = {"source_ip": addr[0], "source_port": str(addr[1])}

                decoded = data.decode("utf-8")
                if self.validator is not None:
                    validated, errors = self.validator.get_validated_object(
                        decoded, line_no=1
                    )

                    if validated is None:
                        raise ValueError(f"Validation failed: {errors}")

                    obj = validated.data
                    headers["origin"] = validated.origin
                else:
                    obj = json.loads(decoded)

                message = json.dumps(
                    obj, ensure_ascii=False, separators=(",", ":")
                ).encode("utf-8")

                logger.info(
                    "Sending into %s message_len=%s message_type=%s headers=%s",
                    self.topic,
                    len(message),
                    type(message).__name__,
                    headers,
                )

                self.publisher.publish(self.topic, message, headers=headers)
            except Exception as e:
                logger.error("UDP message processing failed: %s", e)

                if self.on_decode_error:
                    self.on_decode_error(data, e)

    def close(self) -> None:
        logger.info(f"Closing UDP server {self.ip}:{self.port}")

        self.socket.close()
