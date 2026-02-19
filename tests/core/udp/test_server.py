import json
import socket
import threading
import time

from core.udp.server import UdpServer
from core.validate import Validator
from stream_handler import LS1000Parser, JsonStreamNormalizer
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
        validator = Validator(
            schema_path=static_file("udp_schema.json"),
            origin="test-origin",
        )
        json_normalizer = JsonStreamNormalizer(origin="test-origin")
        server, thread, ip, port = _start_server(
            publisher,
            validator=validator,
            json_normalizer=json_normalizer,
        )

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
        envelope = json.loads(message.decode("utf-8"))
        assert envelope["schema_version"] == "1.0"
        assert envelope["event_type"] == "position"
        assert envelope["origin"] == "test-origin"
        assert envelope["normalized"] is True
        assert isinstance(envelope["ingested_at_ms"], int)
        payload = envelope["payload"]
        assert payload["origin"] == "test-origin"
        assert payload["source_type"] == "json"
        assert payload["tag_id"] == "1"
        assert isinstance(payload["ts_utc_ms"], int)
        assert payload["x"] is None
        assert payload["y"] is None

        assert headers == {
            "source_ip": source_ip,
            "source_port": str(source_port),
            "origin": "test-origin",
            "parser": "json-normalizer",
        }

    def test_on_decode_error_called_and_message_skipped(self, static_file):
        publisher = DoomyPublisher()
        errors = []

        def on_decode_error(data, exc):
            errors.append((data, exc))

        server, thread, ip, port = _start_server(
            publisher,
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

    def test_ls1000_parser_handles_display_message_before_json_validation(self):
        publisher = DoomyPublisher()
        parser = LS1000Parser()
        server, thread, ip, port = _start_server(
            publisher,
            parser=parser,
        )

        payload_bytes = b"display:68,00A320,1614,1700000000123,2,9.65,3.27,1.50"

        try:
            source_ip, source_port = _send_datagram(payload_bytes, ip, port)
            _wait_for_messages(publisher, "test-topic", 1)
        finally:
            _stop_server(server, thread)

        messages = publisher.get_messages()["test-topic"]
        assert len(messages) == 1

        message, headers = messages[0]
        envelope = json.loads(message.decode("utf-8"))
        assert envelope["schema_version"] == "1.0"
        assert envelope["event_type"] == "position"
        assert envelope["origin"] == "ls-1000"
        assert envelope["normalized"] is True
        payload = envelope["payload"]
        assert payload["source_type"] == "display"
        assert payload["origin"] == "ls-1000"
        assert payload["tag_id"] == "00A320"
        assert payload["ts_utc_ms"] == 1700000000123
        assert payload["layer"] == 2
        assert payload["x"] == 9.65
        assert payload["y"] == 3.27
        assert payload["z"] == 1.5

        assert headers == {
            "source_ip": source_ip,
            "source_port": str(source_port),
            "origin": "ls-1000",
            "parser": "ls1000",
        }

    def test_ls1000_parser_falls_back_to_schema_validator(self, static_file):
        publisher = DoomyPublisher()
        parser = LS1000Parser()
        validator = Validator(
            schema_path=static_file("udp_schema.json"),
            origin="test-origin",
        )
        json_normalizer = JsonStreamNormalizer(origin="test-origin")
        server, thread, ip, port = _start_server(
            publisher,
            parser=parser,
            validator=validator,
            json_normalizer=json_normalizer,
        )

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
        envelope = json.loads(message.decode("utf-8"))
        assert envelope["schema_version"] == "1.0"
        assert envelope["event_type"] == "position"
        assert envelope["origin"] == "test-origin"
        assert envelope["normalized"] is True
        payload = envelope["payload"]
        assert payload["origin"] == "test-origin"
        assert payload["source_type"] == "json"
        assert payload["tag_id"] == "1"
        assert isinstance(payload["ts_utc_ms"], int)
        assert headers == {
            "source_ip": source_ip,
            "source_port": str(source_port),
            "origin": "test-origin",
            "parser": "json-normalizer",
        }
