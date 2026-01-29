import time

import pytest

from core.udp.client import UdpClient
from tests.conftest import UdpTestServer


class TestUdpClient:
    """Tests for UdpClient class."""

    def test_send_single_object(self, udp_server: UdpTestServer):
        objects = [{"tag": 1, "value": "test"}]

        with UdpClient(udp_server.ip, udp_server.port) as client:
            client.send(objects, batch_size=1, time_between_batches=0)

        time.sleep(0.1)

        received = udp_server.get_json_messages()

        assert len(received) == 1
        assert received[0] == {"tag": 1, "value": "test"}

    def test_send_multiple_objects(self, udp_server: UdpTestServer):
        objects = [
            {"tag": 1, "data": "first"},
            {"tag": 2, "data": "second"},
            {"tag": 3, "data": "third"},
        ]

        with UdpClient(udp_server.ip, udp_server.port) as client:
            client.send(objects, batch_size=3, time_between_batches=0)

        time.sleep(0.1)

        received = udp_server.get_json_messages()

        assert len(received) == 3
        assert received == objects

    def test_send_with_batching(self, udp_server: UdpTestServer):
        objects = [{"id": i} for i in range(5)]

        with UdpClient(udp_server.ip, udp_server.port) as client:
            client.send(objects, batch_size=2, time_between_batches=0)

        time.sleep(0.1)

        received = udp_server.get_json_messages()
        assert len(received) == 5
        assert received == objects

    def test_send_empty_list(self, udp_server: UdpTestServer):
        with UdpClient(udp_server.ip, udp_server.port) as client:
            client.send([], batch_size=1, time_between_batches=0)

        time.sleep(0.1)

        assert len(udp_server.messages) == 0

    def test_send_unicode_data(self, udp_server: UdpTestServer):
        objects = [{"tag": 1, "message": "Привет мир!"}]

        with UdpClient(udp_server.ip, udp_server.port) as client:
            client.send(objects, batch_size=1, time_between_batches=0)

        time.sleep(0.1)

        received = udp_server.get_json_messages()

        assert len(received) == 1
        assert received[0]["message"] == "Привет мир!"

    def test_context_manager(self, udp_server: UdpTestServer):
        with UdpClient(udp_server.ip, udp_server.port) as client:
            assert client.socket is not None
            assert client.socket.fileno() != -1

        assert client.socket.fileno() == -1

    def test_manual_close(self, udp_server: UdpTestServer):
        client = UdpClient(udp_server.ip, udp_server.port)
        assert client.socket.fileno() != -1

        client.close()
        assert client.socket.fileno() == -1


class TestUdpClientErrors:
    def test_send_after_close_raises(self, udp_server: UdpTestServer):
        client = UdpClient(udp_server.ip, udp_server.port)
        client.close()

        with pytest.raises(OSError):
            client.send([{"tag": 1}], batch_size=1, time_between_batches=0)
