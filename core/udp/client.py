import json
import socket
import logging

from itertools import batched
from time import sleep
from typing import List, Any

logger = logging.getLogger(__name__)


class UdpClient:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

        logger.info(f"Creating UDP socket {self.ip}:{self.port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(
        self, objects: List[Any], batch_size: int, time_between_batches: int
    ) -> None:
        for batch in batched(objects, batch_size):
            for object in batch:
                s = json.dumps(object, ensure_ascii=False, separators=(",", ":"))
                payload = s.encode("utf-8")

                try:
                    self.socket.sendto(payload, (self.ip, self.port))
                except socket.error as e:
                    logger.error("Error sending message: %s", e)
                    raise

            sleep(time_between_batches)
            logger.info(
                f"Sent {len(batch)} objects at {batch_size} objects per {time_between_batches} seconds"
            )

    def close(self) -> None:
        logger.info(f"Closing UDP socket {self.ip}:{self.port}")
        self.socket.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
