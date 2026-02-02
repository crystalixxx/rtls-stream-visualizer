import json
import socket
import threading
import time

from core.udp.server import UdpServer
from tests.conftest import DoomyPublisher


def _start_server(publisher, **kwargs):
    server = UdpServer(
        "127.0.0.1",
        0,
        publisher,
        topic="test-topic",
        **kwargs,
    )

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    ip, port = server.socket.getsockname()

    return server, thread, ip, port


def _stop_server(server, thread):
    server.close()
    thread.join(timeout=1.0)


def _send_datagram(payload: bytes, ip: str, port: int):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(("127.0.0.1", 0))
    client.sendto(payload, (ip, port))

    source_ip, source_port = client.getsockname()
    client.close()

    return source_ip, source_port


def _wait_for_messages(publisher, topic, expected_len, timeout=1.0):
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if len(publisher.get_messages().get(topic, [])) >= expected_len:
            return

        time.sleep(0.01)

    raise AssertionError(f"Timed out waiting for {expected_len} messages on {topic}")


def _wait_for_errors(errors, expected_len, timeout=1.0):
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if len(errors) >= expected_len:
            return

        time.sleep(0.01)

    raise AssertionError(f"Timed out waiting for {expected_len} decode errors")


class TestUdpServer:
    def test_publish_json_payload_reencodes_and_adds_headers(self, static_file):
        publisher = DoomyPublisher()
        server, thread, ip, port = _start_server(publisher, parse_json=True)

        payload_path = static_file("pretty_payload.json")
        payload_bytes = payload_path.read_bytes()

        try:
            source_ip, source_port = _send_datagram(payload_bytes, ip, port)
            _wait_for_messages(publisher, "test-topic", 1)
        finally:
            _stop_server(server, thread)

        messages = publisher.get_messages()["test-topic"]
        assert len(messages) == 1

        message, headers = messages[0]
        obj = json.loads(payload_bytes.decode("utf-8"))

        expected = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )

        assert message == expected
        assert message != payload_bytes

        assert headers == {
            "source_ip": source_ip,
            "source_port": str(source_port),
        }

    def test_publish_raw_payload_when_parse_json_false(self, static_file):
        publisher = DoomyPublisher()
        server, thread, ip, port = _start_server(publisher, parse_json=False)

        payload_bytes = static_file("raw_payload.txt").read_bytes()

        try:
            source_ip, source_port = _send_datagram(payload_bytes, ip, port)
            _wait_for_messages(publisher, "test-topic", 1)
        finally:
            _stop_server(server, thread)

        messages = publisher.get_messages()["test-topic"]
        assert len(messages) == 1

        message, headers = messages[0]

        assert message == payload_bytes
        assert headers == {
            "source_ip": source_ip,
            "source_port": str(source_port),
        }

    def test_on_decode_error_called_and_message_skipped(self, static_file):
        publisher = DoomyPublisher()
        errors = []

        def on_decode_error(data, exc):
            errors.append((data, exc))

        server, thread, ip, port = _start_server(
            publisher,
            parse_json=True,
            on_decode_error=on_decode_error,
        )

        payload_bytes = static_file("invalid_payload.json").read_bytes()

        try:
            _send_datagram(payload_bytes, ip, port)
            _wait_for_errors(errors, 1)
        finally:
            _stop_server(server, thread)

        assert len(errors) == 1
        assert errors[0][0] == payload_bytes

        assert isinstance(errors[0][1], Exception)
        assert publisher.get_messages().get("test-topic", []) == []
