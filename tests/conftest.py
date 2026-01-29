import json
import logging
import socket
import threading
from pathlib import Path
from typing import List

import pytest


def pytest_configure(config):
    """
    Called after command line options have been parsed and all plugins loaded.
    This is the right place to set up logging before tests run.
    """
    from core.logging_config import setup_logging

    setup_logging(level=logging.DEBUG)


@pytest.fixture
def static_file(request):
    """
    Fixture to get path to static test files.

    Looks for files in two locations (in order):
    1. test_dir/static/{test_name}/{filename} - test-specific files
    2. test_dir/static/{filename} - common files shared between tests
    """
    test_dir = Path(request.fspath).parent
    test_name = request.node.name

    def get_path(filename: str) -> Path:
        test_specific = test_dir / "static" / test_name / filename
        if test_specific.exists():
            return test_specific

        common = test_dir / "static" / filename
        if common.exists():
            return common

        raise FileNotFoundError(
            f"File '{filename}' not found in:\n"
            f"  - {test_specific}\n"
            f"  - {common}"
        )

    return get_path


# =============================================================================
# UDP Test Utilities
# =============================================================================


class UdpTestServer:
    """
    Simple UDP server for testing that collects received messages.

    Usage:
        server = UdpTestServer()
        server.start()
        # ... send messages to server.ip:server.port ...
        messages = server.get_json_messages()
        server.stop()
    """

    def __init__(self, ip: str = "127.0.0.1", port: int = 0):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, port))
        self.socket.settimeout(1.0)

        self.ip, self.port = self.socket.getsockname()

        self.messages: List[bytes] = []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._thread.start()

    def _receive_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                data, _ = self.socket.recvfrom(65535)
                self.messages.append(data)
            except socket.timeout:
                continue
            except OSError:
                break

    def stop(self) -> None:
        self._stop_event.set()
        self.socket.close()

        if self._thread:
            self._thread.join(timeout=2.0)

    def get_json_messages(self) -> List[dict]:
        return [json.loads(msg.decode("utf-8")) for msg in self.messages]

    def clear(self) -> None:
        self.messages.clear()


@pytest.fixture
def udp_server():
    server = UdpTestServer()

    server.start()

    yield server

    server.stop()


@pytest.fixture
def udp_client(udp_server):
    from core.udp.client import UdpClient

    client = UdpClient(udp_server.ip, udp_server.port)

    yield client

    client.close()
